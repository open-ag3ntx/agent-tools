#!/usr/bin/env node
/**
 * Validate Postman collection structure and best practices
 */

const fs = require('fs');

function validateCollection(filePath) {
    const collection = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const issues = [];
    
    // Check collection info
    if (!collection.info || !collection.info.name) {
        issues.push('❌ Collection must have a name');
    }
    
    if (!collection.info || !collection.info.description) {
        issues.push('⚠️  Collection should have a description');
    }
    
    // Check items
    if (!collection.item || collection.item.length === 0) {
        issues.push('❌ Collection has no items');
    }
    
    // Validate each request
    validateItems(collection.item, issues);
    
    // Report results
    if (issues.length === 0) {
        console.log('✅ Collection validation passed');
        return true;
    } else {
        console.log('Collection validation issues:');
        issues.forEach(issue => console.log(issue));
        return false;
    }
}

function validateItems(items, issues, depth = 0) {
    items.forEach(item => {
        if (item.item) {
            // It's a folder
            if (!item.name) {
                issues.push(`❌ Folder at depth ${depth} missing name`);
            }
            validateItems(item.item, issues, depth + 1);
        } else if (item.request) {
            // It's a request
            validateRequest(item, issues, depth);
        }
    });
}

function validateRequest(item, issues, depth) {
    if (!item.name) {
        issues.push(`❌ Request at depth ${depth} missing name`);
    }
    
    if (!item.request.url) {
        issues.push(`❌ Request "${item.name}" missing URL`);
    }
    
    // Check for hardcoded values
    const url = JSON.stringify(item.request.url);
    if (url.includes('localhost') || url.includes('127.0.0.1')) {
        issues.push(`⚠️  Request "${item.name}" has hardcoded localhost URL`);
    }
    
    // Check for tests
    if (!item.event || !item.event.some(e => e.listen === 'test')) {
        issues.push(`⚠️  Request "${item.name}" has no test scripts`);
    }
}

if (process.argv.length < 3) {
    console.log('Usage: node validate_collection.js <collection.json>');
    process.exit(1);
}

const result = validateCollection(process.argv[2]);
process.exit(result ? 0 : 1);