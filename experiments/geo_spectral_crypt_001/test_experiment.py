import unittest
import numpy as np
from experiment import shift,conjugate,signature,encrypt,decrypt,run

class Test(unittest.TestCase):
 def test_similarity_sweep(self):
  for n in range(2,26):
   for k in range(1,n):
    self.assertEqual(signature(shift(n,k)),signature(conjugate(shift(n,k),n+k)))
 def test_prime(self):self.assertEqual(signature(shift(7,3))[2],0)
 def test_composite(self):self.assertEqual(signature(shift(9,3))[2],9)
 def test_roundtrip(self):
  A=shift(9,3);rows,key=encrypt(A)
  self.assertTrue(np.array_equal(A,decrypt(rows,key,9)))
 def test_randomized_nonces(self):
  A=shift(7,3);a,key=encrypt(A);b,_=encrypt(A,key)
  self.assertNotEqual(a,b)
 def test_fixed_ciphertext_lengths(self):
  a,_=encrypt(shift(12,4));self.assertEqual(len({len(ct) for _,ct in a}),1)
 def test_every_case(self):
  for row in run():
   self.assertTrue(row['traces_equal_under_relabeling'])
   self.assertTrue(row['plaintext_operator_recovered_after_decryption'])
   self.assertTrue(row['fresh_ciphertext_differs'])
   self.assertTrue(row['ciphertext_lengths_fixed'])
if __name__=='__main__':unittest.main()
