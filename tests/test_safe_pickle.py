"""Unit tests for SafeUnpickler security mechanism."""

import os
import pickle
import unittest
import numpy as np
import pandas as pd

from node_inspect.core.safe_pickle import safe_load_pickle, PickleSecurityError


class MaliciousExploit:
    """Simulates an arbitrary code execution exploit via pickle."""
    def __reduce__(self):
        return (os.system, ("echo EXPLOIT_TRIGGERED",))


class MaliciousEvalExploit:
    """Simulates code execution via builtins.eval."""
    def __reduce__(self):
        return (eval, ("1 + 1",))


class TestSafePickle(unittest.TestCase):
    def test_safe_primitives_and_containers(self):
        """Test that standard safe types load properly."""
        data = {
            "name": "NodeInspect",
            "version": 1.0,
            "tags": ["gui", "debug", "python"],
            "meta": {"nested": True, "count": 42},
            "tuple": (1, 2, 3),
        }
        pickled = pickle.dumps(data)
        loaded = safe_load_pickle(pickled)
        self.assertEqual(loaded, data)

    def test_safe_numpy(self):
        """Test that NumPy arrays can be safely loaded."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        pickled = pickle.dumps(arr)
        loaded = safe_load_pickle(pickled)
        self.assertTrue(isinstance(loaded, np.ndarray))
        np.testing.assert_array_equal(loaded, arr)

    def test_safe_pandas(self):
        """Test that Pandas DataFrames can be safely loaded."""
        df = pd.DataFrame({"colA": [10, 20, 30], "colB": ["x", "y", "z"]})
        pickled = pickle.dumps(df)
        loaded = safe_load_pickle(pickled)
        self.assertTrue(isinstance(loaded, pd.DataFrame))
        pd.testing.assert_frame_equal(loaded, df)

    def test_blocks_malicious_os_system(self):
        """Verify that pickle containing os.system is strictly blocked."""
        malicious_data = pickle.dumps(MaliciousExploit())
        with self.assertRaises(PickleSecurityError) as ctx:
            safe_load_pickle(malicious_data)
        self.assertIn(ctx.exception.module, ("os", "nt", "posix"))

    def test_blocks_malicious_eval(self):
        """Verify that eval is blocked."""
        malicious_data = pickle.dumps(MaliciousEvalExploit())
        with self.assertRaises(PickleSecurityError):
            safe_load_pickle(malicious_data)


if __name__ == "__main__":
    unittest.main()
