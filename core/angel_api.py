import pyotp
import urllib.request
from SmartApi import SmartConnect
from core.logger import get_logger
from config import settings

logger = get_logger()

class AngelOneAPI:
    def __init__(self):
        self.api_key = settings.API_KEY
        self.client_id = settings.CLIENT_ID
        self.password = settings.PASSWORD
        self.totp_secret = settings.TOTP_SECRET
        self.smart_api = None
        self.refresh_token = None
        self.feed_token = None

    def _get_totp(self):
        if not self.totp_secret:
            logger.error("TOTP Secret is missing.")
            return None
        try:
            totp = pyotp.TOTP(self.totp_secret).now()
            return totp
        except Exception as e:
            logger.error(f"Error generating TOTP: {e}")
            return None

    def get_public_ip(self):
        try:
            return urllib.request.urlopen("https://api.ipify.org").read().decode("utf8")
        except Exception as e:
            logger.error(f"Failed to get public IP: {e}")
            return "127.0.0.1"

    def get_mac_address(self):
        import uuid
        return ":".join(["{:02x}".format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])

    def connect(self):
        logger.info("Initializing Angel One Smart API connection...")
        try:
            self.smart_api = SmartConnect(api_key=self.api_key)
            totp = self._get_totp()
            if not totp:
                raise ValueError("Could not generate TOTP.")
                
            data = self.smart_api.generateSession(
                self.client_id, 
                self.password, 
                totp
            )
            
            if data['status']:
                self.refresh_token = data['data']['refreshToken']
                self.feed_token = self.smart_api.getfeedToken()
                logger.info("Successfully authenticated with Angel One Smart API", extra={"client_id": self.client_id})
                
                user_profile = self.smart_api.getProfile(self.refresh_token)
                logger.info("User Profile Loaded", extra={"profile": user_profile['data']['name']})
                return True
            else:
                logger.error(f"Login failed: {data['message']}")
                return False
                
        except Exception as e:
            logger.exception("An exception occurred during Angel One authentication.")
            return False

    def logout(self):
        if self.smart_api:
            try:
                logout_data = self.smart_api.terminateSession(self.client_id)
                logger.info(f"Logout successful: {logout_data}")
            except Exception as e:
                logger.error(f"Logout failed: {e}")

angel_api = AngelOneAPI()
