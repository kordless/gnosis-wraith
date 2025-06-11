#!/usr/bin/env python3
"""
Gnosis Wraith Safe Cleanup Script
Executes only the safest cleanup operations
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class SafeCleanup:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.archive_dir = None
        self.stats = {
            'files_removed': 0,
            'dirs_removed': 0,
            'space_freed': 0,
            'files_archived': 0
        }
    
    def create_archive_dir(self):
        """Create timestamped archive directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.archive_dir = self.base_dir / f"archive_cleanup_{timestamp}"
        self.archive_dir.mkdir(exist_ok=True)
        print(f"Created archive directory: {self.archive_dir}")
        return self.archive_dir
    
    def calculate_size(self, path):
        """Calculate size of file or directory"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return 0
    
    def clean_python_cache(self):
        """Remove all Python cache files and directories"""
        print("\n1. Cleaning Python cache files...")
        
        # Remove __pycache__ directories
        for cache_dir in self.base_dir.rglob("__pycache__"):
            if cache_dir.exists():
                size = self.calculate_size(cache_dir)
                shutil.rmtree(cache_dir)
                self.stats['dirs_removed'] += 1
                self.stats['space_freed'] += size
                print(f"   Removed: {cache_dir.relative_to(self.base_dir)}")
        
        # Remove .pyc files
        for pyc_file in self.base_dir.rglob("*.pyc"):
            if pyc_file.exists():
                size = pyc_file.stat().st_size
                pyc_file.unlink()
                self.stats['files_removed'] += 1
                self.stats['space_freed'] += size
        
        # Remove .pyo files
        for pyo_file in self.base_dir.rglob("*.pyo"):
            if pyo_file.exists():
                size = pyo_file.stat().st_size
                pyo_file.unlink()
                self.stats['files_removed'] += 1
                self.stats['space_freed'] += size
    
    def clean_extension_backups(self):
        """Archive old extension files"""
        print("\n2. Cleaning extension backup files...")
        
        ext_dir = self.base_dir / "gnosis_wraith" / "extension"
        if not ext_dir.exists():
            print("   Extension directory not found, skipping...")
            return
        
        # Archive backup files
        backup_dir = self.archive_dir / "extension_backups"
        backup_dir.mkdir(exist_ok=True)
        
        patterns = ["*.backup", "*.new", "popup_v2.*", "background_v2.js"]
        for pattern in patterns:
            for file in ext_dir.glob(pattern):
                if file.exists():
                    size = file.stat().st_size
                    dest = backup_dir / file.name
                    shutil.move(str(file), str(dest))
                    self.stats['files_archived'] += 1
                    self.stats['space_freed'] += size
                    print(f"   Archived: {file.name}")
    
    def archive_old_reports(self):
        """Archive old test reports"""
        print("\n3. Archiving old test reports...")
        
        reports_dir = self.base_dir / "storage" / "reports"
        if not reports_dir.exists():
            print("   Reports directory not found, skipping...")
            return
        
        # Archive old reports
        old_reports_dir = self.archive_dir / "old_reports"
        old_reports_dir.mkdir(exist_ok=True)
        
        patterns = [
            "Web_Crawl_Report_*",
            "Screenshot_of_*",
            "Image_Analysis_Report_*"
        ]
        
        for pattern in patterns:
            for file in reports_dir.glob(pattern):
                if file.exists() and file.is_file():
                    size = file.stat().st_size
                    dest = old_reports_dir / file.name
                    shutil.move(str(file), str(dest))
                    self.stats['files_archived'] += 1
                    self.stats['space_freed'] += size
        
        print(f"   Archived {self.stats['files_archived']} old reports")
    
    def archive_duplicate_images(self):
        """Archive duplicate images from reports/images"""
        print("\n4. Archiving duplicate images...")
        
        images_dir = self.base_dir / "storage" / "reports" / "images"
        if not images_dir.exists():
            print("   Images directory not found, skipping...")
            return
        
        # Archive images
        dup_images_dir = self.archive_dir / "duplicate_images"
        dup_images_dir.mkdir(exist_ok=True)
        
        count = 0
        for img in images_dir.glob("*.png"):
            if img.exists():
                size = img.stat().st_size
                dest = dup_images_dir / img.name
                shutil.move(str(img), str(dest))
                count += 1
                self.stats['space_freed'] += size
        
        if count > 0:
            print(f"   Archived {count} duplicate images")
            self.stats['files_archived'] += count
    
    def remove_empty_directories(self):
        """Remove known empty directories"""
        print("\n5. Removing empty directories...")
        
        empty_dirs = ["server", "search", "host-files"]
        
        for dir_name in empty_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # Check if truly empty
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    self.stats['dirs_removed'] += 1
                    print(f"   Removed empty directory: {dir_name}/")
    
    def create_gitignore(self):
        """Create or update .gitignore file"""
        print("\n6. Updating .gitignore...")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.pyc
*.pyo
.Python
.pytest_cache/
.coverage
.hypothesis/

# Virtual Environment
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Project specific
local_datastore/
storage/logs/*.log
storage/reports/
storage/screenshots/
*.backup
*.new
*.tmp
archive_cleanup_*/

# Environment
.env
.env.local
.env.*.local

# Dependencies
node_modules/
"""
        
        gitignore_path = self.base_dir / ".gitignore"
        
        # Backup existing .gitignore if it exists
        if gitignore_path.exists():
            backup_path = self.archive_dir / "gitignore.backup"
            shutil.copy2(gitignore_path, backup_path)
            print("   Backed up existing .gitignore")
        
        # Write new .gitignore
        gitignore_path.write_text(gitignore_content)
        print("   Created comprehensive .gitignore file")
    
    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "="*50)
        print("CLEANUP SUMMARY")
        print("="*50)
        print(f"Files removed: {self.stats['files_removed']}")
        print(f"Directories removed: {self.stats['dirs_removed']}")
        print(f"Files archived: {self.stats['files_archived']}")
        print(f"Space freed: {self.stats['space_freed'] / 1024 / 1024:.2f} MB")
        print(f"\nArchive location: {self.archive_dir}")
        print("\n✅ Safe cleanup completed successfully!")
    
    def run(self):
        """Execute safe cleanup operations"""
        print("Starting Gnosis Wraith Safe Cleanup...")
        print("This will only perform safe operations that won't break functionality.")
        
        # Create archive directory
        self.create_archive_dir()
        
        # Execute cleanup operations
        self.clean_python_cache()
        self.clean_extension_backups()
        self.archive_old_reports()
        self.archive_duplicate_images()
        self.remove_empty_directories()
        self.create_gitignore()
        
        # Print summary
        self.print_summary()

def main():
    """Main entry point"""
    print("="*50)
    print("GNOSIS WRAITH SAFE CLEANUP")
    print("="*50)
    
    response = input("\nThis will clean Python cache and archive old files. Continue? (y/n): ")
    
    if response.lower() == 'y':
        cleanup = SafeCleanup()
        cleanup.run()
        
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("1. Test the application to ensure everything works")
        print("2. Check browser extension functionality")
        print("3. Review archived files before permanent deletion")
        print("4. Commit changes to git")
    else:
        print("Cleanup cancelled.")

if __name__ == "__main__":
    main()
