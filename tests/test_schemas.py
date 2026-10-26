from app.schemas import GroceryItem, ReceiptExtraction


def test_grocery_item_validates_confidence():
    item = GroceryItem(
        name="Rice",
        quantity=2,
        unit="lb",
        confidence=0.95,
        source_text="Rice 2 LB",
    )
    assert item.name == "Rice"
    assert item.quantity == 2


def test_receipt_extraction_contains_items():
    result = ReceiptExtraction(
        items=[
            GroceryItem(
                name="Rice",
                quantity=2,
                unit="lb",
                confidence=0.95,
                source_text="Rice 2 LB",
            )
        ]
    )
    assert len(result.items) == 1
    assert result.items[0].name == "Rice"
