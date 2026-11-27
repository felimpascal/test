import tempfile
import unittest
from pathlib import Path
from app import create_app
class Smoke(unittest.TestCase):
    def test_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=create_app(Path(tmp)/'db.sqlite').test_client()
            central={'Authorization':'Bearer central'}
            north={'Authorization':'Bearer north'}
            self.assertEqual(c.post('/receipts',headers=central,json={'sku':'A','quantity':20}).status_code,201)
            r=c.post('/requests',headers=north,json={'reference':'R1','lines':[{'sku':'A','quantity':3}]})
            self.assertEqual(r.status_code,201)
            rid=r.json['id']
            self.assertEqual(c.post(f'/requests/{rid}/approve',headers=central).status_code,200)
            self.assertEqual(c.post(f'/requests/{rid}/dispatch',headers=central).status_code,200)
            self.assertEqual(c.get('/report',headers=north).json[0]['physical'],3)
if __name__=='__main__':
    unittest.main()
