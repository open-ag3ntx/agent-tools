# Todo Management Guidelines

You have access to todo management tools to track progress during complex, multi-step tasks.

## When to Use Todos

Use todos for any task with 3+ steps or tasks that take significant time to complete:
- Multi-step coding projects
- Data processing pipelines
- Research and analysis tasks
- Deployment task_groups
- Any sequential process where tracking matters

## task_group

1. **Plan**: Break down the task and create todos for each major step
2. **Execute**: Work through todos one by one
3. **Track**: Update each todo to "completed" immediately after finishing it
4. **Verify**: List todos before declaring the task complete

## Tool Usage

- `create_todo(title, task_group)` - Create a step at the start of work
- `list_todos(task_group)` - Check what's pending/completed
- `update_todo(task_group, todo_id, status)` - Mark as "completed" or "cancelled" 
- `delete_todo(task_group, title)` - Only for correcting mistakes

## Key Rules
Create all todos BEFORE starting work
Update todos IMMEDIATELY after completing each step
Use clear, action-oriented titles ("Set up Tailwind CSS" not "Tailwind")
Use consistent task_group names for related todo
Don't skip todo creation for multi-step tasks
Don't forget to update todos as you progress
Don't use delete for marking work done (use update_todo instead)
## Example

**Task**: Build and deploy a Next.js app
```
1. Create todos:
   - "Initialize Next.js project"
   - "Configure Tailwind and shadcn/ui"
   - "Build app features"
   - "Deploy to Vercel"
2. Execute each step, updating status after completion

3. List todos to verify all are completed
```
Use todos to stay organized and ensure no steps are missed in complex task_groups.