import os
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError,VerificationError
ph=PasswordHasher()
def verify_password(password:str)->bool:
    h=os.environ.get('PANEL_PASSWORD_HASH','')
    if not h:return False
    try:return ph.verify(h,password)
    except (VerifyMismatchError,VerificationError):return False
