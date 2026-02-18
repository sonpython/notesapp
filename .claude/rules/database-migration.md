# Database Migration Rules

## MANDATORY for ALL Schema Changes

Before ANY database schema modification:

1. **Create Migration Plan**
   - Document current schema state
   - List all affected tables/columns
   - Identify data at risk
   - Plan rollback strategy

2. **Data Preservation Checklist**
   - [ ] Backup existing data before migration
   - [ ] Test migration on copy of production data
   - [ ] Verify row counts before/after
   - [ ] Check foreign key constraints
   - [ ] Validate data integrity post-migration

3. **Migration Types**

   | Type | Risk | Approach |
   |------|------|----------|
   | Add column (nullable) | Low | Direct migration |
   | Add column (NOT NULL) | Medium | Add nullable → backfill → set NOT NULL |
   | Drop column | High | Verify unused → soft delete → hard delete |
   | Rename column | High | Add new → copy data → drop old |
   | Change type | High | Add new column → migrate data → swap |
   | Drop table | Critical | Full backup → verify no references → drop |

4. **Alembic Migration Template**
   ```python
   def upgrade():
       # 1. Create backup/temp structures if needed
       # 2. Add new schema elements
       # 3. Migrate data
       # 4. Remove old elements (if safe)

   def downgrade():
       # MUST be reversible
       # Restore original schema
   ```

5. **Testing Requirements**
   - Run migration on empty DB
   - Run migration on DB with test data
   - Verify all API endpoints work
   - Check for orphaned data

## NEVER
- Drop columns/tables without data backup
- Use `--sql` mode without reviewing generated SQL
- Skip `downgrade()` implementation
- Migrate production without staging test
