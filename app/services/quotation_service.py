from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models


def create_quotation(db: Session, quotation_data):

    # -----------------------------
    # Validate Client
    # -----------------------------
    client = db.query(models.Client).filter(
        models.Client.id == quotation_data.client_id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # -----------------------------
    # Create Empty Quotation First
    # -----------------------------
    quotation = models.Quotation(
        client_id=quotation_data.client_id,
        travel_date=quotation_data.travel_date,
        pax=quotation_data.pax,
        grand_discount=Decimal(str(quotation_data.grand_discount)),
        grand_net_total=Decimal("0"),
        final_selling=Decimal("0"),
        total_profit=Decimal("0")
    )

    db.add(quotation)
    db.flush()  # Important: get quotation.id before commit

    grand_net_total = Decimal("0")
    grand_selling_total = Decimal("0")

    # -----------------------------
    # Process Each Item
    # -----------------------------
    for item in quotation_data.items:

        service = db.query(models.Service).filter(
            models.Service.id == item.service_id
        ).first()

        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"Service ID {item.service_id} not found"
            )

        # Get latest valid rate
        rate = db.query(models.ServiceRate).filter(
            models.ServiceRate.service_id == service.id
        ).first()

        if not rate:
            raise HTTPException(
                status_code=404,
                detail=f"No rate found for service ID {service.id}"
            )

        cost = Decimal(str(rate.cost))
        margin_percent = Decimal(str(item.margin_percent))
        units = item.units

        selling_price = cost + (cost * margin_percent / 100)

        total_net = cost * units
        total_selling = selling_price * units
        profit = total_selling - total_net

        grand_net_total += total_net
        grand_selling_total += total_selling

        # -----------------------------
        # SAVE QUOTATION ITEM
        # -----------------------------
        quotation_item = models.QuotationItem(
            quotation_id=quotation.id,
            service_id=service.id,
            service_name=service.name,
            supplier_name=None,  # You can enhance later
            cost=cost,
            selling_price=selling_price,
            margin_percent=margin_percent,
            units=units,
            total_net=total_net,
            total_selling=total_selling,
            profit=profit
        )

        db.add(quotation_item)

    # -----------------------------
    # Apply Discount
    # -----------------------------
    discount = Decimal(str(quotation_data.grand_discount or 0))
    final_selling = grand_selling_total - discount
    total_profit = final_selling - grand_net_total

    quotation.grand_net_total = grand_net_total
    quotation.final_selling = final_selling
    quotation.total_profit = total_profit

    db.commit()
    db.refresh(quotation)

    return quotation
