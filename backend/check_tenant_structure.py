from app.db.session import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    try:
        # Vérifier la structure de la table tenant
        result = db.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'tenant' ORDER BY ordinal_position"))
        columns = result.fetchall()
        
        print("=== STRUCTURE DE LA TABLE TENANT ===")
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
            
        # Vérifier s'il y a des tenants existants
        result = db.execute(text("SELECT * FROM tenant"))
        tenants = result.fetchall()
        print(f"\nTenants existants: {len(tenants)}")
        for tenant in tenants:
            print(f"  {tenant}")
            
    finally:
        db.close()

if __name__ == '__main__':
    main()