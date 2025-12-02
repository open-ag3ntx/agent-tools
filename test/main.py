
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from database import init_db, get_db_connection
import sqlite3
from auth import get_password_hash, verify_password, create_access_token, verify_token

# Pydantic Models
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Initialize the database when the application starts
init_db()

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, hashed_password FROM users WHERE username = ?", (form_data.username,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_in_db = UserInDB(**user_data)

    if not verify_password(form_data.password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_in_db.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, hashed_password FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data is None:
        raise credentials_exception
    return UserInDB(**user_data)

@app.get("/")
async def read_root(current_user: UserInDB = Depends(get_current_user)):
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
async def health_check(current_user: UserInDB = Depends(get_current_user)):
    return {"status": "ok"}

@app.post("/users/", response_model=UserBase)
async def create_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = get_password_hash(user.password)
    try:
        cursor.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (user.username, hashed_password))
        conn.commit()
        return {"message": "User created successfully", "username": user.username}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already registered")
    finally:
        conn.close()

@app.get("/users/")
async def get_users(current_user: UserInDB = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return {"users": [dict(user) for user in users]}

@app.get("/users/{user_id}")
async def get_user(user_id: int, current_user: UserInDB = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"user": dict(user)}
    raise HTTPException(status_code=404, detail="User not found")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"user": dict(user)}
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}")
async def update_user(user_id: int, username: str = None, password: str = None, current_user: UserInDB = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    updates = []
    params = []
    if username:
        updates.append("username = ?")
        params.append(username)
    if password:
        hashed_password = get_password_hash(password)
        updates.append("hashed_password = ?")
        params.append(hashed_password)

    if not updates:
        conn.close()
        return {"message": "No updates provided"}

    set_clause = ", ".join(updates)
    params.append(user_id)
    
    try:
        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", tuple(params))
        conn.commit()
        conn.close()
        return {"message": "User updated successfully", "user_id": user_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    updates = []
    params = []
    if name:
        updates.append("name = ?")
        params.append(name)
    if email:
        updates.append("email = ?")
        params.append(email)

    if not updates:
        conn.close()
        return {"message": "No updates provided"}

    set_clause = ", ".join(updates)
    params.append(user_id)
    
    try:
        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", tuple(params))
        conn.commit()
        conn.close()
        return {"message": "User updated successfully", "user_id": user_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: UserInDB = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    if rows_affected:
        return {"message": "User deleted successfully", "user_id": user_id}
    raise HTTPException(status_code=404, detail="User not found")
