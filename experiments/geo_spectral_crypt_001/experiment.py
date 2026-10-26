"""Spectral invariance and encryption control, standard-library version.

AES-GCM encryption comparison implemented by optional cryptography package in
local benchmark; CI installs that dependency explicitly.
"""
import hashlib, json, secrets
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def shift(n,k):
    return np.array([[int(j==(i+k)%n) for j in range(n)] for i in range(n)],dtype=int)

def signature(A):
    return tuple(int(np.trace(np.linalg.matrix_power(A,t))) for t in range(1,len(A)+1))

def conjugate(A,seed):
    p=np.random.default_rng(seed).permutation(len(A))
    return A[np.ix_(p,p)]

def encrypt(A,key=None):
    key=key or AESGCM.generate_key(bit_length=256)
    aes=AESGCM(key); rows=[]
    for i in range(len(A)):
        j=int(np.flatnonzero(A[i])[0])
        nonce=secrets.token_bytes(12)
        rows.append((nonce,aes.encrypt(nonce,f'{i:04d}:{j:04d}'.encode(),None)))
    return rows,key

def decrypt(rows,key,n):
    aes=AESGCM(key);A=np.zeros((n,n),dtype=int)
    for nonce,ct in rows:
        i,j=map(int,aes.decrypt(nonce,ct,None).decode().split(':'))
        A[i,j]=1
    return A

def run():
    result=[]
    for n,k in [(7,1),(7,3),(9,1),(9,3),(12,4)]:
        A=shift(n,k);B=conjugate(A,n+k)
        a,key=encrypt(A);b,_=encrypt(A,key)
        result.append({'n':n,'k':k,'traces_equal_under_relabeling':signature(A)==signature(B),
          'plaintext_operator_recovered_after_decryption':np.array_equal(A,decrypt(a,key,n)),
          'fresh_ciphertext_differs':a!=b,'ciphertext_lengths_fixed':len({len(ct) for _,ct in a+b})==1,
          'trace_vector':signature(A)})
    return result

if __name__=='__main__':print(json.dumps(run(),indent=2))
