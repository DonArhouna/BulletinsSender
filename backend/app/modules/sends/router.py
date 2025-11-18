from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app import deps
from app.modules.sends import crud, schemas, invoice
from app.modules import sends as sends_module
from app.modules.subscriptions import models as subs_models
from app.modules.users import models as user_models
from app.modules.emails import service as email_service_module, schemas as email_schemas
from fastapi.responses import FileResponse
import os

router = APIRouter()


@router.post("/sends/", response_model=schemas.Send)
def create_send(
    *,
    send_in: schemas.SendCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Create an Envoi (Send). Calculates the total automatically from the user's subscription/forfait.
    A facture PDF is generated in background and the `invoice_path` is stored on the Send.
    """
    try:
        send_obj = crud.send.create(db, obj_in=send_in, user_id=current_user.id, tenant_id=current_user.tenant_id)

        # Generate invoice in background
        background_tasks.add_task(invoice.generate_invoice_pdf, db, send_obj.id)

        return send_obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sends/", response_model=List[schemas.Send])
def list_sends(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """List sends for the current user (client view) or all tenant sends (admin)."""
    if current_user.is_superuser:
        sends = crud.send.get_multi(db, skip=skip, limit=limit)
    else:
        sends = crud.send.get_multi(db, skip=skip, limit=limit, user_id=current_user.id)

    # Convert to dict and add pricing_plan relation
    result = []
    for send in sends:
        send_dict = {
            "id": send.id,
            "user_id": send.user_id,
            "tenant_id": send.tenant_id,
            "user_subscription_id": send.user_subscription_id,
            "pricing_plan_id": send.pricing_plan_id,
            "nb_bulletins": send.nb_bulletins,
            "price_per_bulletin": send.price_per_bulletin,
            "total_amount": send.total_amount,
            "invoice_path": send.invoice_path,
            "invoice_number": send.invoice_number,
            "invoice_date": send.invoice_date,
            "status": send.status,
            "created_at": send.created_at,
        }

        # Add pricing_plan relation if exists
        if send.pricing_plan_id:
            pricing_plan = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == send.pricing_plan_id).first()
            if pricing_plan:
                send_dict["pricing_plan"] = {
                    "id": pricing_plan.id,
                    "price_per_bulletin": pricing_plan.price_per_bulletin,
                    "currency": pricing_plan.currency
                }

        result.append(send_dict)

    return result


@router.get("/sends/{send_id}", response_model=schemas.Send)
def get_send(
    send_id: int,
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    send_obj = crud.send.get(db, id=send_id)
    if not send_obj:
        raise HTTPException(status_code=404, detail="Send not found")
    if (send_obj.user_id != current_user.id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return send_obj



@router.get("/sends/{send_id}/invoice")
def download_invoice(
    send_id: int,
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Download the invoice PDF for a send if allowed."""
    send_obj = crud.send.get(db, id=send_id)
    if not send_obj:
        raise HTTPException(status_code=404, detail="Send not found")
    if (send_obj.user_id != current_user.id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not send_obj.invoice_path:
        # Try to generate if missing
        try:
            invoice.generate_invoice_pdf(db, send_obj.id)
            db.refresh(send_obj)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Invoice not found and generation failed: {e}")

    return FileResponse(send_obj.invoice_path, filename=os.path.basename(send_obj.invoice_path))


@router.post("/sends/{send_id}/invoice/send")
def send_invoice_by_email(
    send_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Send invoice by email to the owner of the send (background).

    Only owner or admin can trigger.
    """
    send_obj = crud.send.get(db, id=send_id)
    if not send_obj:
        raise HTTPException(status_code=404, detail="Send not found")
    if (send_obj.user_id != current_user.id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Ensure invoice exists
    if not send_obj.invoice_path:
        try:
            invoice.generate_invoice_pdf(db, send_obj.id)
            db.refresh(send_obj)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invoice generation failed: {e}")

    # Prepare email payload
    recipient = current_user.email if current_user.email else None
    if not recipient:
        raise HTTPException(status_code=400, detail="User has no email to send invoice to")

    def _send_invoice_task(path: str, recipient_email: str, send_id: int):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            email_in = email_schemas.EmailCreate(
                subject=f"Facture SendBulletin #{send_obj.invoice_number}",
                body=f"Bonjour,\n\nVeuillez trouver en pièce jointe la facture #{send_obj.invoice_number} pour l'envoi {send_obj.id}.\n\nCordialement,\nSendBulletin",
                recipient_email=recipient_email,
                sender_email=None,
            )
            # Use internal method to send bytes as PDF
            email_service_module.email_service.send_bulletin_email_with_content(email_in, content, os.path.basename(path))
        except Exception as e:
            print(f"Failed to send invoice email: {e}")

    # Schedule background task
    background_tasks.add_task(_send_invoice_task, send_obj.invoice_path, recipient, send_obj.id)

    return {"message": "Invoice will be sent by email in background"}
