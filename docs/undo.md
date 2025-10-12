# BumpCalver Undo Documentation

## Overview

BumpCalver now includes powerful undo functionality that allows you to revert version bump operations. This feature automatically creates backups of files before modification and maintains a history of operations that can be undone.

## Features

- **Automatic Backups**: Files are automatically backed up before any version changes
- **Operation History**: Complete history of version operations with metadata
- **Git Integration**: Can undo git commits and tags created during version bumps
- **Safety Validation**: Checks for potential conflicts before undoing operations
- **Selective Undo**: Undo specific operations by ID or just the latest operation

## CLI Commands

### List Operation History

View recent version bump operations that can be undone:

```bash
bumpcalver --list-history
```

Example output:
```
Recent operations (showing last 10):
--------------------------------------------------------------------------------
 1. 2025-10-12 14:30:15 | 2025.10.12.003 | 3 file(s) [TAG] [COMMIT]
    ID: 20251012_143015_123
 2. 2025-10-12 14:25:10 | 2025.10.12.002 | 2 file(s) [TAG]
    ID: 20251012_142510_456
 3. 2025-10-12 14:20:05 | 2025.10.12.001 | 1 file(s)
    ID: 20251012_142005_789
--------------------------------------------------------------------------------
Use 'bumpcalver --undo' to undo the latest operation
Use 'bumpcalver --undo-id <operation_id>' to undo a specific operation
```

### Undo Latest Operation

Undo the most recent version bump operation:

```bash
bumpcalver --undo
```

This will:
1. Restore all modified files from their backups
2. Delete any git tags that were created
3. Reset git commits (if auto-commit was used)

### Undo Specific Operation

Undo a specific operation by its ID:

```bash
bumpcalver --undo-id 20251012_143015_123
```

## How It Works

### Backup Process

When you run a version bump command, BumpCalver automatically:

1. **Creates Backups**: Before modifying any files, creates timestamped backups in `.bumpcalver/backups/`
2. **Records Metadata**: Stores operation details in `bumpcalver-history.json` (root level) including:
   - Timestamp and operation ID
   - New version number
   - List of files modified
   - Git operations performed (tags, commits)
   - Backup file locations

3. **Performs Update**: Executes the version bump as normal
4. **Saves History**: Updates the history file for future undo operations

### Undo Process

When you undo an operation, BumpCalver:

1. **Validates Safety**: Checks if files have been modified since the backup
2. **Restores Files**: Copies backup files over the current versions
3. **Undoes Git Operations**:
   - Deletes git tags that were created
   - Resets git commits (if they match the recorded commit hash)

## Safety Features

### Validation Checks

Before performing an undo, BumpCalver validates:

- Backup files still exist
- Original files haven't been significantly modified since backup
- Git repository state is consistent

### Warning Messages

You may see warnings like:
- `File example.py may have been modified since backup` - File was changed after the version bump
- `Backup file not found` - The backup file has been deleted or moved
- `Current HEAD is not the expected commit` - Git history has changed since the operation

### Conflict Resolution

If warnings are detected, the undo operation will still proceed but may not be complete. You can:

1. **Review Changes**: Check what files were restored vs. what couldn't be restored
2. **Manual Restoration**: Manually fix any files that couldn't be automatically restored
3. **Git Operations**: Manually undo git operations if they couldn't be automatically reverted

## Configuration

### Backup Storage

Backups and history are stored as follows:

```
your-project/
├── bumpcalver-history.json         # Operation history (root level)
├── .bumpcalver/
│   └── backups/
│       ├── 20251012_143015_123_file1.py   # Timestamped backups
│       ├── 20251012_143015_124_file2.toml
│       └── ...
├── your-source-files...
└── pyproject.toml
```

### History Limits

- **Operation Limit**: Keeps last 50 operations to prevent unbounded growth
- **File Cleanup**: Old backup files can be cleaned up automatically
- **Storage Location**: Customize backup directory location if needed

### Cleanup

Remove old backups (older than 30 days):

```python
from bumpcalver.backup_utils import BackupManager

backup_manager = BackupManager()
backup_manager.cleanup_old_backups(days_to_keep=30)
```

## Integration Examples

### Basic Workflow

```bash
# Make a version bump
bumpcalver --build --git-tag

# List recent operations
bumpcalver --list-history

# Undo if needed
bumpcalver --undo
```

### CI/CD Integration

```bash
# Version bump with safety net
bumpcalver --build --git-tag --auto-commit

# If tests fail, undo the version bump
if [ $? -ne 0 ]; then
    echo "Tests failed, undoing version bump"
    bumpcalver --undo
    exit 1
fi
```

### Development Workflow

```bash
# Experimental version bump
bumpcalver --custom "experimental"

# Test changes...

# If experiment fails, undo
bumpcalver --undo

# If experiment succeeds, make real version bump
bumpcalver --build --git-tag
```

## Limitations

- **Git Repository**: Git undo operations only work within git repositories
- **File Permissions**: Backup/restore operations respect file system permissions
- **External Changes**: Cannot undo changes made by external tools after the version bump
- **Backup Storage**: Backup files consume disk space (cleaned up automatically)

## Troubleshooting

### Common Issues

**"No operations found in history"**
- No version bump operations have been performed yet
- History file may have been deleted

**"Backup file not found"**
- Backup files may have been manually deleted
- Check `.bumpcalver/backups/` directory

**"Current HEAD is not the expected commit"**
- Git history has changed since the version bump
- Manual git operations may be needed

**"File may have been modified since backup"**
- File was edited after the version bump
- Review changes before proceeding with undo

### Recovery

If undo operations fail, you can manually:

1. **Restore Files**: Copy backup files from `.bumpcalver/backups/`
2. **Check History**: Review `history.json` for operation details
3. **Git Operations**: Manually delete tags or reset commits using git commands

## Best Practices

1. **Regular Cleanup**: Periodically clean up old backups to save disk space
2. **Version Control**: Ensure your project is under git version control for full undo capabilities
3. **Testing**: Test undo functionality in a development environment first
4. **Backup Backups**: Consider backing up the `.bumpcalver/` directory in critical environments
5. **Review Changes**: Always review what changes will be undone before proceeding

## Version Control Integration

### Recommended .gitignore Entries

Add these entries to your `.gitignore` file to exclude backup and history files from version control:

```gitignore
# BumpCalver backup and history files
.bumpcalver/
bumpcalver-history.json
```

This ensures that:
- Backup files remain local to each developer/environment
- History doesn't clutter your repository
- Sensitive or large backup files aren't committed
- Each environment maintains its own undo history
