from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.db.session import SessionLocal
from app.modules.emails import models
from app.modules.users import models as user_models  # ensure Tenant/User are registered

def run():
    db: Session = SessionLocal()
    try:
        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind is not None else ""
        print("Dialect:", dialect_name)
        if dialect_name == "sqlite":
            year_expr = func.strftime('%Y', models.Email.created_at)
            month_expr = func.strftime('%m', models.Email.created_at)
            q = (
                db.query(
                    year_expr.label('year'),
                    month_expr.label('month'),
                    func.count(models.Email.id).label('total_count'),
                    func.sum(case((models.Email.status.in_(['sent','success']), 1), else_=0)).label('sent_count'),
                    func.sum(case((models.Email.status.in_(['failed','error']), 1), else_=0)).label('failed_count'),
                    func.max(models.Email.created_at).label('latest_date')
                )
                .group_by(year_expr, month_expr)
                .order_by(year_expr.desc(), month_expr.desc())
                .limit(3)
            )
        else:
            period_expr = func.date_trunc('month', models.Email.created_at)
            q = (
                db.query(
                    period_expr.label('period'),
                    func.count(models.Email.id).label('total_count'),
                    func.sum(case((models.Email.status.in_(['sent','success']), 1), else_=0)).label('sent_count'),
                    func.sum(case((models.Email.status.in_(['failed','error']), 1), else_=0)).label('failed_count'),
                    func.max(models.Email.created_at).label('latest_date')
                )
                .group_by(period_expr)
                .order_by(period_expr.desc())
                .limit(3)
            )
        print("SQL:", str(q.statement.compile(compile_kwargs={"literal_binds": True})))
        rows = q.all()
        print("Rows:", rows)
    except Exception as e:
        print("Error:", repr(e))
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run()