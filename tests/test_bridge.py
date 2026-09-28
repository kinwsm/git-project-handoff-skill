import asyncio
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import unittest
from app_server import Handoffs

class FakeServer:
    def __init__(self, fail=False):
        self.calls=[]
        self.fail=fail
    async def start(self): pass
    async def call(self, method, params):
        self.calls.append(method)
        if method=='thread/start': return {'thread':{'id':'test-thread'}}
        if self.fail: raise TimeoutError('uncertain send')
        return {'turn':{'id':'test-turn'}}

class DeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_repeat_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            server=FakeServer()
            h=Handoffs(Path(tmp)/'test.sqlite',server,root=tmp)
            first=await h.send('request_123','Test')
            repeat=await h.send('request_123','Test')
            self.assertEqual(first['thread_id'],repeat['thread_id'])
            self.assertTrue(repeat['duplicate'])
            with self.assertRaises(ValueError): await h.send('request_123','Different')
            self.assertEqual(server.calls,['thread/start','thread/name/set','turn/start'])
            h.db.close()
    async def test_uncertain_send_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.sqlite'
            server=FakeServer(True)
            h=Handoffs(path,server,root=tmp)
            result=await h.send('request_456','Test')
            self.assertEqual(result['status'],'unknown')
            h.db.close()
            fresh=FakeServer()
            h=Handoffs(path,fresh,root=tmp)
            result=await h.send('request_456','Test')
            self.assertTrue(result['duplicate'])
            self.assertEqual(fresh.calls,[])
            with self.assertRaises(ValueError): await h.status('not_ours')
            h.db.close()

if __name__=='__main__': unittest.main()
