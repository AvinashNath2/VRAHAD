from sys import version_info
from os import urandom
from base64 import b64encode,b64decode
from json import dumps,loads,load
from Crypto.PublicKey import RSA
from sqlalchemy import create_engine
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from sqlalchemy.orm import sessionmaker
from models import LicenseKey,Base
from Crypto.Cipher import AES
from Crypto import Random
from time import time

AadhaarURL = load(open('config.json'))['NirAadhaarURL']

py_ver = version_info[0]

if py_ver == 3:
	from urllib.request import Request, urlopen
	from urllib.parse import urlencode
elif py_ver == 2:
	from urllib2 import Request, urlopen
	from urllib import urlencode

def encryptPid(PID="", path='CERTS/public.pub',passphrase='VRAHAD'):
	'''
	Returns encrypted PID Node.
	'''
	pub_obj = RSA.importKey(open(path,'r').read(),passphrase=passphrase)
	Enc = pub_obj.encrypt(PID,32)[0]
	return b64encode(Enc)

def encryptHmac(key="", text=""):
	if ((key != "") and (text !="")):
		padded = text + bytes((32 - len(text) % 32) * chr(32 - len(text) % 32),'utf-8')
		iv = Random.new().read(AES.block_size)
		cipher = AES.new(key, AES.MODE_CBC, iv)
		return b64encode(iv + cipher.encrypt(text))
	else:
		return ""

def getCertificate(field,cert_path='CERTS/certificate.crt'):
	'''
	Returns Digital Certificate's expiry date ( Used for ci ) and the Certificate body.
	'''
	cert_raw = open(cert_path,'rt').read()
	cert = load_certificate(FILETYPE_PEM, cert_raw)
	if field == "expiry":
		return cert.get_notAfter()
	elif field == "raw":
		return '\n'.join(open(cert_path,'rt').read().split('\n')[1:-2])

def getTID(**kwargs):
	'''
	Returns Mock Terminal ID for a deivce
	`Actual Code should be implemented to get the TID from the terminal`
	'''
	return "TEST_TID"

def getUDC(**kwargs):
	'''
	Returns Mock Unique Device Code which is made by-
	Vendor ID (4 Digits) + DateOfDeployment(YYMMDD) (6 digits) + Serial(10 digits)
	'''
	return "XXXX111111XXXXXXXXXX"

def getFDC(is_Fingerprint,**kwargs):
	'''
	Returns Mock Fingerprint Device Code.
	Else NA if no Fingerprinting is needed for request.
	'''
	if is_Fingerprint:
		return "FFFFFFFFFF"
	else:
		return "NA"

def getIDC(is_Iris,**kwargs):
	'''
	Returns Mock Iris Device Code.
	Else NA if no Iris is needed for request.
	'''
	if is_Iris:
		return "IIIIIIIIII"
	else:
		return "NA"

def getPIP(**kwargs):
	'''
	Returns Public IP address by pinging to ip.42.pl
	'''
	try:
		url = "http://ip.42.pl/raw"
		return urlopen(Request(url)).read().decode('utf-8')
	except:
		return "NA"

def getLatLngAlt():
	'''
	Returns Mock LatLngAlt string.
	`Actual code should be implemeted if GPS is available`
	'''
	lat = "26.5393" # 15 chars
	lon = "80.4878" # 15 chars max
	alt = "98" # 7 chars in meters
	return ','.join([lat,lon,alt])

def getLOV(lot,**kwargs):
	'''
	Returns Mock LOV value based on LOT.
	If it is P then Pincode else LatLngAlt if it is G.
	'''
	if lot == "G":
		return getLatLngAlt()
	elif lot == "P":
		return "209801"

def getTxnID(aua,uid):
	'''
	Creates a mock Transaction ID corresponding to a UID
	'''
	return str(int(time()))+uid+aua

def getSkey(path='CERTS/public.pub',passphrase='VRAHAD'):
	'''
	Returns Session Key encrypted with the public key given by UIDAI to AUA.
	'''
	# It must not be stored anywhere except for RAM
	# AES256 is the actual session key
	_AES256key = urandom(32)
	# Encrypt the AES256 key with the public Key
	pub_obj = RSA.importKey(open(path,'r').read(),passphrase=passphrase)
	Skey = pub_obj.encrypt(_AES256key,32)[0]
	return _AES256key,b64encode(Skey)

def getOTP(is_otp,ver,ac,uid_0,uid_1,asalk):
	'''
	Fetches latest OTP for a UID from UIDAI Server.
	'''
	if is_otp:
		URL = AadhaarURL+('/'.join(['otp',ver,ac,uid_0,uid_1,asalk]))
		print(URL)
	else:
		return None

def getPIN(is_pin):
	'''
	Returns a Mock uid Pin.
	'''
	if is_pin:
		return "XXXXXX"
	else:
		return ""



def getLicenseKey(asa):
	'''
	Returns, updates and creates the LicenseKey lk by requesting it from UIDAI Server.
	'''
	url = AadhaarURL+"getLicenseKey/"+asa
	engine = create_engine('sqlite:///lkd.db')
	Base.metadata.bind = engine
	DBSession = sessionmaker(bind=engine)
	session = DBSession()
	lKey = session.query(LicenseKey).one()
	if lKey:
		# If licenseKey exists then retrieve it.
		# check if it is valid
		if (int(time()) - int(lKey.ts)) < 3600:
			return lKey.lk
		else:
			lkey = loads(urlopen(Request(url)).read().decode('utf-8'))
			lKey.ts = int(time())
			lKey.lk = lkey
			session.commit()
			return lkey
	else:
		# If licenseKey does not exist then retrieve it from aadhaar server
		# and save it in DB and return it
		lkey = loads(urlopen(Request(url)).read().decode('utf-8'))
		session.add(LicenseKey(lk = lkey , ts=int(time())))
		session.commit()
		return lkey

if __name__ == "__main__":
	print(getCertificate("raw"))
