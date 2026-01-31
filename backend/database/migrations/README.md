# Database Migrations

This directory contains SQL migration files for setting up and modifying the Supabase database schema.

## How to Use

1. **Apply migrations**: Run each migration file in order in the Supabase SQL Editor
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor
   - Copy and paste the contents of each migration file
   - Execute in order (001, 002, 003, etc.)

2. **Modify the schema**: 
   - **Yes, you can change migrations later!**
   - To modify the schema, create a new migration file (e.g., `002_add_new_column.sql`)
   - Follow the naming convention: `XXX_description.sql` where XXX is a sequential number
   - Document your changes in the migration file header
   - Run the new migration in Supabase SQL Editor

## Migration Files

- `001_initial_schema.sql` - Initial database setup with papers and paper_chunks tables

## Best Practices

1. **Never modify existing migration files** - Always create new ones
2. **Test migrations** - Run migrations on a test database first if possible
3. **Document changes** - Include clear comments explaining what each migration does
4. **Version control** - Keep all migration files in git for tracking

## Example: Adding a New Column

If you want to add a new column later, create `002_add_author_column.sql`:

```sql
-- Migration: 002_add_author_column.sql
-- Description: Add author field to papers table
-- Created: 2024-01-XX

ALTER TABLE papers 
ADD COLUMN author TEXT;

CREATE INDEX IF NOT EXISTS papers_author_idx ON papers(author);
```

Then run it in Supabase SQL Editor.
