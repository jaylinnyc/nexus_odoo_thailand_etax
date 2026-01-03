"""
Odoo API Client Helper
"""
import xmlrpc.client
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY


class OdooClient:
    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.api_key = ODOO_API_KEY
        self.uid = None
        self.models = None
        self.connect()
    
    def connect(self):
        """Authenticate and connect to Odoo"""
        common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common', allow_none=True)
        self.uid = common.authenticate(self.db, self.username, self.api_key, {})
        
        if not self.uid:
            raise Exception("Authentication failed")
        
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', allow_none=True)
        print(f"✅ Connected to Odoo (User ID: {self.uid})")
        
        # Get server version
        version_info = common.version()
        print(f"📌 Server: {version_info.get('server_version', 'Unknown')}")
        return True
    
    def execute(self, model, method, *args, **kwargs):
        """Execute a method on a model"""
        return self.models.execute_kw(
            self.db, self.uid, self.api_key,
            model, method, args, kwargs
        )
    
    def search_read(self, model, domain=None, fields=None, limit=None):
        """Search and read records"""
        domain = domain or []
        kwargs = {'fields': fields} if fields else {}
        if limit:
            kwargs['limit'] = limit
        return self.execute(model, 'search_read', domain, **kwargs)
    
    def get_fields(self, model):
        """Get all fields for a model"""
        return self.search_read(
            'ir.model.fields',
            [('model', '=', model)],
            ['name', 'field_description', 'ttype', 'required', 'readonly']
        )
    
    def get_model_info(self, model):
        """Get model information"""
        return self.search_read(
            'ir.model',
            [('model', '=', model)],
            ['name', 'model', 'info']
        )


if __name__ == '__main__':
    # Test connection
    client = OdooClient()
    print("\n✅ Connection test successful!")
