from typing import Dict, Any

class BasePaymentProvider:
    name: str = "Base"
    
    def process(self, order: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic process method. Should return a success/failure status.
        """
        raise NotImplementedError("Each provider must implement process()")

class StripeProvider(BasePaymentProvider):
    name: str = "Stripe"
    
    def process(self, order: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for Stripe API
        print(f"Processing Stripe payment for order {getattr(order, 'id', 'unknown')}")
        return {"status": "success", "provider": self.name}

class TabbyProvider(BasePaymentProvider):
    name: str = "Tabby"
    
    def process(self, order: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for Tabby API
        print(f"Processing Tabby payment for order {getattr(order, 'id', 'unknown')}")
        return {"status": "success", "provider": self.name}

class TamaraProvider(BasePaymentProvider):
    name: str = "Tamara"
    
    def process(self, order: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for Tamara API
        print(f"Processing Tamara payment for order {getattr(order, 'id', 'unknown')}")
        return {"status": "success", "provider": self.name}

class CODProvider(BasePaymentProvider):
    name: str = "Cash on Delivery"
    
    def process(self, order: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        print(f"Processing COD for order {getattr(order, 'id', 'unknown')}")
        return {"status": "success", "provider": self.name}

class PaymentRegistry:
    def __init__(self):
        self._providers = {
            'card': StripeProvider(),
            'tabby': TabbyProvider(),
            'tamara': TamaraProvider(),
            'cod': CODProvider(),
        }

    def get_provider(self, method_name):
        return self._providers.get(method_name)

payment_registry = PaymentRegistry()
