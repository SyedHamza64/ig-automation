"""
Database health check and schema validation
"""
import logging
from typing import Dict, List, Any
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.account import Account
from app.models.profile import Profile

logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    """Validates database schema matches model definitions"""
    
    def __init__(self):
        self.expected_columns = {
            'accounts': self._get_model_columns(Account),
            'profiles': self._get_model_columns(Profile),
        }
    
    def _get_model_columns(self, model_class) -> List[str]:
        """Get expected columns from SQLAlchemy model"""
        return [column.name for column in model_class.__table__.columns]
    
    def validate_schema(self) -> Dict[str, Any]:
        """Validate database schema against model definitions"""
        db = next(get_db())
        try:
            results = {
                'status': 'healthy',
                'errors': [],
                'warnings': [],
                'tables_checked': []
            }
            
            for table_name, expected_columns in self.expected_columns.items():
                try:
                    # Check if table exists
                    table_exists = db.execute(
                        text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"),
                        {"table_name": table_name}
                    ).scalar()
                    
                    if not table_exists:
                        results['errors'].append(f"Table '{table_name}' does not exist")
                        results['status'] = 'unhealthy'
                        continue
                    
                    # Get actual columns from database
                    actual_columns_result = db.execute(
                        text("SELECT column_name FROM information_schema.columns WHERE table_name = :table_name ORDER BY column_name"),
                        {"table_name": table_name}
                    )
                    actual_columns = [row[0] for row in actual_columns_result]
                    
                    # Check for missing columns
                    missing_columns = set(expected_columns) - set(actual_columns)
                    if missing_columns:
                        results['errors'].append(f"Table '{table_name}' missing columns: {', '.join(missing_columns)}")
                        results['status'] = 'unhealthy'
                    
                    # Check for extra columns (warnings only)
                    extra_columns = set(actual_columns) - set(expected_columns)
                    if extra_columns:
                        results['warnings'].append(f"Table '{table_name}' has extra columns: {', '.join(extra_columns)}")
                    
                    results['tables_checked'].append({
                        'table': table_name,
                        'expected_columns': len(expected_columns),
                        'actual_columns': len(actual_columns),
                        'status': 'ok' if not missing_columns else 'error'
                    })
                    
                except Exception as e:
                    results['errors'].append(f"Error checking table '{table_name}': {str(e)}")
                    results['status'] = 'unhealthy'
            
            return results
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'errors': [f"Database connection failed: {str(e)}"],
                'warnings': [],
                'tables_checked': []
            }
        finally:
            db.close()
    
    def check_and_log(self) -> bool:
        """Run health check and log results"""
        results = self.validate_schema()
        
        if results['status'] == 'healthy':
            logger.info("Database schema validation passed")
            if results['warnings']:
                for warning in results['warnings']:
                    logger.warning(f"Schema warning: {warning}")
            return True
        else:
            logger.error("Database schema validation failed:")
            for error in results['errors']:
                logger.error(f"  - {error}")
            return False

# Global instance
db_health_checker = DatabaseHealthChecker()

def validate_database_on_startup():
    """Validate database schema on application startup"""
    logger.info("Running database schema validation...")
    if not db_health_checker.check_and_log():
        logger.error("Database schema validation failed. Please run migrations or fix schema issues.")
        # Don't exit the application, just log the error
        # In production, you might want to exit or send alerts
    else:
        logger.info("Database schema validation completed successfully")
