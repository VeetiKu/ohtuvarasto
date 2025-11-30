import unittest
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, init_db, DATABASE  # pylint: disable=wrong-import-position


class TestWarehouseApp(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
        if os.path.exists(DATABASE):
            os.unlink(DATABASE)

    def test_index_empty(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse Management', response.data)
        self.assertIn(b'No warehouses found', response.data)

    def test_create_warehouse(self):
        response = self.client.post('/warehouse/new', data={
            'name': 'Test Warehouse',
            'location': 'Helsinki',
            'capacity': '100'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Warehouse', response.data)

    def test_view_warehouse(self):
        self.client.post('/warehouse/new', data={
            'name': 'My Warehouse',
            'location': 'Espoo',
            'capacity': '50'
        })
        response = self.client.get('/warehouse/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Warehouse', response.data)
        self.assertIn(b'Espoo', response.data)

    def test_edit_warehouse(self):
        self.client.post('/warehouse/new', data={
            'name': 'Old Name',
            'location': 'Old Location',
            'capacity': '10'
        })
        response = self.client.post('/warehouse/1/edit', data={
            'name': 'New Name',
            'location': 'New Location',
            'capacity': '20'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Name', response.data)

    def test_delete_warehouse(self):
        self.client.post('/warehouse/new', data={
            'name': 'To Delete',
            'location': '',
            'capacity': '10'
        })
        response = self.client.post(
            '/warehouse/1/delete',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'To Delete', response.data)

    def test_add_item(self):
        self.client.post('/warehouse/new', data={
            'name': 'Item Warehouse',
            'location': '',
            'capacity': '100'
        })
        response = self.client.post('/warehouse/1/item/new', data={
            'name': 'Test Item',
            'quantity': '5',
            'description': 'A test item'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Item', response.data)

    def test_edit_item(self):
        self.client.post('/warehouse/new', data={
            'name': 'Item Warehouse',
            'location': '',
            'capacity': '100'
        })
        self.client.post('/warehouse/1/item/new', data={
            'name': 'Old Item',
            'quantity': '5',
            'description': ''
        })
        response = self.client.post('/warehouse/1/item/1/edit', data={
            'name': 'Updated Item',
            'quantity': '10',
            'description': 'Updated description'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Updated Item', response.data)

    def test_delete_item(self):
        self.client.post('/warehouse/new', data={
            'name': 'Item Warehouse',
            'location': '',
            'capacity': '100'
        })
        self.client.post('/warehouse/1/item/new', data={
            'name': 'Item to Remove',
            'quantity': '3',
            'description': ''
        })
        response = self.client.post(
            '/warehouse/1/item/1/delete',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Item to Remove', response.data)

    def test_new_warehouse_form(self):
        response = self.client.get('/warehouse/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Warehouse', response.data)

    def test_edit_warehouse_form(self):
        self.client.post('/warehouse/new', data={
            'name': 'Warehouse',
            'location': '',
            'capacity': '10'
        })
        response = self.client.get('/warehouse/1/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Warehouse', response.data)

    def test_new_item_form(self):
        self.client.post('/warehouse/new', data={
            'name': 'Warehouse',
            'location': '',
            'capacity': '10'
        })
        response = self.client.get('/warehouse/1/item/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Item', response.data)

    def test_edit_item_form(self):
        self.client.post('/warehouse/new', data={
            'name': 'Warehouse',
            'location': '',
            'capacity': '10'
        })
        self.client.post('/warehouse/1/item/new', data={
            'name': 'Item',
            'quantity': '5',
            'description': ''
        })
        response = self.client.get('/warehouse/1/item/1/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Item', response.data)

    def test_view_nonexistent_warehouse(self):
        response = self.client.get('/warehouse/999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse Management', response.data)

    def test_edit_nonexistent_warehouse(self):
        response = self.client.get('/warehouse/999/edit', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse Management', response.data)

    def test_new_item_nonexistent_warehouse(self):
        response = self.client.get(
            '/warehouse/999/item/new',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse Management', response.data)

    def test_edit_nonexistent_item(self):
        self.client.post('/warehouse/new', data={
            'name': 'Warehouse',
            'location': '',
            'capacity': '10'
        })
        response = self.client.get(
            '/warehouse/1/item/999/edit',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Warehouse', response.data)
