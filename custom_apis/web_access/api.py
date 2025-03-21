"""Web access API for Createve.AI API Server."""

import base64
import html2text
import json
import re
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, List, Optional, Tuple, Union
import urllib.parse

import validators
from urllib.parse import urlparse
import threading
from datetime import datetime, timedelta
import json
import os
import pickle
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class ActionStep:
    """Represents a single action step in a sequence."""
    action: str
    url: str
    selector: str
    input_value: Optional[str] = None
    wait_time: int = 5
    selector_type: str = "css"
    verify_ssl: bool = True

@dataclass
class ActionSequence:
    """Represents a sequence of actions with state validation."""
    name: str
    steps: List[ActionStep]
    created_at: float
    updated_at: float
    state_checks: Dict[int, Dict[str, Any]] = None

@dataclass
class SessionState:
    """Represents persistent session state."""
    session: requests.Session
    created: datetime
    last_used: datetime
    cookies: Dict
    headers: Dict
    action_sequences: Dict[str, ActionSequence] = None

# Global session store with lock
_SESSIONS: Dict[str, SessionState] = {}
_SESSIONS_LOCK = threading.Lock()
_SESSION_TIMEOUT = 3600  # 1 hour timeout
_MAX_SESSIONS = 1000
_SESSION_FILE = "web_access_sessions.pkl"

def _save_sessions():
    """Save sessions to disk for persistence."""
    with _SESSIONS_LOCK:
        session_data = {}
        for sid, state in _SESSIONS.items():
            # Convert requests.Session to dict of cookies and headers
            session_data[sid] = {
                "created": state.created,
                "last_used": state.last_used,
                "cookies": state.cookies,
                "headers": state.headers,
                "action_sequences": state.action_sequences
            }
        
        with open(_SESSION_FILE, 'wb') as f:
            pickle.dump(session_data, f)

def _load_sessions():
    """Load sessions from disk on startup."""
    if os.path.exists(_SESSION_FILE):
        with open(_SESSION_FILE, 'rb') as f:
            try:
                session_data = pickle.load(f)
                now = datetime.now()
                
                with _SESSIONS_LOCK:
                    for sid, data in session_data.items():
                        # Only restore non-expired sessions
                        if now - data["last_used"] <= timedelta(seconds=_SESSION_TIMEOUT):
                            session = requests.Session()
                            session.cookies.update(data["cookies"])
                            session.headers.update(data["headers"])
                            
                            _SESSIONS[sid] = SessionState(
                                session=session,
                                created=data["created"],
                                last_used=data["last_used"],
                                cookies=data["cookies"],
                                headers=data["headers"],
                                action_sequences=data["action_sequences"]
                            )
            except Exception:
                # Start fresh if there's any error loading sessions
                pass

# Load sessions on module import
_load_sessions()

def _cleanup_sessions():
    """Remove expired sessions and save to disk."""
    now = datetime.now()
    with _SESSIONS_LOCK:
        expired = [
            sid for sid, session_data in _SESSIONS.items()
            if now - session_data.last_used > timedelta(seconds=_SESSION_TIMEOUT)
        ]
        for sid in expired:
            del _SESSIONS[sid]
        
        # Save after cleanup
        _save_sessions()

def _validate_url(url: str) -> bool:
    """Validate URL format and scheme."""
    if not validators.url(url):
        return False
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https')

class WebInfoRetriever:
    """Web page information and link retrieval API endpoint."""
    
    CATEGORY = "web_access"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for web info retrieval."""
        return {
            "required": {
                "url": ("STRING", {
                    "multiline": False,
                    "placeholder": "https://example.com"
                }),
            },
            "optional": {
                "wait_for_load": ("INTEGER", {
                    "default": 5,
                    "min": 1,
                    "max": 60,
                    "placeholder": "Wait time in seconds"
                }),
                "extract_links": ("BOOLEAN", {"default": True}),
                "dynamic_load": ("BOOLEAN", {"default": False}),
                "session_id": ("STRING", {
                    "multiline": False,
                    "placeholder": "Session ID for maintaining state"
                }),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("page_info",)
    FUNCTION = "retrieve_info"
    
    def _create_selenium_driver(self):
        """Create a new Selenium WebDriver instance."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def _get_session(self, session_id: Optional[str]) -> requests.Session:
        """Get or create a session for the given ID."""
        if not session_id:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Createve.AI API Client/1.0',
            })
            return session
        
        with _SESSIONS_LOCK:
            # Clean up old sessions
            _cleanup_sessions()
            
            # Check session limit
            if session_id not in _SESSIONS and len(_SESSIONS) >= _MAX_SESSIONS:
                raise ValueError("Maximum number of sessions reached")
            
            now = datetime.now()
            if session_id not in _SESSIONS:
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Createve.AI API Client/1.0',
                })
                _SESSIONS[session_id] = {
                    "session": session,
                    "created": now,
                    "last_used": now
                }
            else:
                _SESSIONS[session_id]["last_used"] = now
                session = _SESSIONS[session_id]["session"]
            
            return session
    
    def retrieve_info(self, url: str, wait_for_load: int = 5,
                     extract_links: bool = True, dynamic_load: bool = False,
                     session_id: Optional[str] = None,
                     verify_ssl: bool = True) -> Tuple[Dict]:
        """
        Retrieve information from a web page.
        
        Args:
            url: The URL to retrieve information from
            wait_for_load: Time to wait for page load in seconds
            extract_links: Whether to extract links from the page
            dynamic_load: Whether to use Selenium for JavaScript-rendered content
            session_id: Optional session ID for maintaining state
            
        Returns:
            Dictionary containing page information
        """
        try:
            result = {
                "url": url,
                "timestamp": time.time(),
                "success": False,
                "error": None
            }
            
            # Validate URL
            if not _validate_url(url):
                raise ValueError("Invalid URL format or scheme")
            
            if dynamic_load:
                # Use Selenium for JavaScript-rendered content
                driver = None
                try:
                    driver = self._create_selenium_driver()
                    driver.get(url)
                    WebDriverWait(driver, wait_for_load).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    page_source = driver.page_source
                    result["title"] = driver.title
                    
                finally:
                    driver.quit()
            else:
                # Use requests for static content
                session = self._get_session(session_id)
                response = session.get(
                    url,
                    timeout=wait_for_load,
                    verify=verify_ssl,
                    headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                response.raise_for_status()
                
                page_source = response.text
                
            # Parse the page content
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Extract basic info
            result["title"] = soup.title.string if soup.title else None
            result["meta_description"] = (
                soup.find("meta", attrs={"name": "description"})["content"]
                if soup.find("meta", attrs={"name": "description"})
                else None
            )
            
            # Convert HTML to plain text
            h = html2text.HTML2Text()
            h.ignore_links = True
            result["text_content"] = h.handle(page_source)
            
            if extract_links:
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = urllib.parse.urljoin(url, href)
                    elif not href.startswith(('http://', 'https://')):
                        href = urllib.parse.urljoin(url, href)
                        
                    links.append({
                        "url": href,
                        "text": link.get_text(strip=True),
                        "title": link.get('title')
                    })
                
                result["links"] = links
            
            result["success"] = True
            
        except ValueError as e:
            result["error"] = str(e)
            result["success"] = False
        except requests.exceptions.RequestException as e:
            result["error"] = "Network error occurred"
            result["success"] = False
        except Exception as e:
            result["error"] = "An unexpected error occurred"
            result["success"] = False
        
        return (result,)

class ActionSequenceManager:
    """Manages sequences of web actions."""
    
    CATEGORY = "web_access"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for action sequence management."""
        return {
            "required": {
                "action": (["create", "execute", "delete", "list"], {"default": "list"}),
                "sequence_name": ("STRING", {
                    "multiline": False,
                    "placeholder": "my-login-sequence"
                }),
            },
            "optional": {
                "session_id": ("STRING", {
                    "multiline": False,
                    "placeholder": "Session ID for state"
                }),
                "steps": ("STRING", {
                    "multiline": True,
                    "placeholder": "JSON array of action steps"
                })
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("sequence_result",)
    FUNCTION = "manage_sequence"
    
    def manage_sequence(self, action: str, sequence_name: str,
                       session_id: Optional[str] = None,
                       steps: Optional[str] = None) -> Tuple[Dict]:
        """
        Manage action sequences (create, execute, delete, list).
        
        Args:
            action: Operation to perform
            sequence_name: Name of the sequence
            session_id: Session ID for state
            steps: JSON array of action steps (for create)
        """
        result = {
            "action": action,
            "sequence_name": sequence_name,
            "timestamp": time.time(),
            "success": False,
            "error": None
        }
        
        try:
            if action == "create" and steps:
                # Parse and validate steps
                step_data = json.loads(steps)
                action_steps = []
                
                for step in step_data:
                    action_steps.append(ActionStep(**step))
                
                sequence = ActionSequence(
                    name=sequence_name,
                    steps=action_steps,
                    created_at=time.time(),
                    updated_at=time.time()
                )
                
                if session_id:
                    with _SESSIONS_LOCK:
                        if session_id in _SESSIONS:
                            if not _SESSIONS[session_id].action_sequences:
                                _SESSIONS[session_id].action_sequences = {}
                            _SESSIONS[session_id].action_sequences[sequence_name] = sequence
                            _save_sessions()
                
                result["success"] = True
                
            elif action == "execute":
                if not session_id or session_id not in _SESSIONS:
                    raise ValueError("Valid session_id required for execution")
                
                sequences = _SESSIONS[session_id].action_sequences
                if not sequences or sequence_name not in sequences:
                    raise ValueError(f"Sequence {sequence_name} not found")
                
                sequence = sequences[sequence_name]
                action_results = []
                
                # Create WebActionPerformer for execution
                performer = WebActionPerformer()
                
                # Execute each step
                for i, step in enumerate(sequence.steps):
                    step_result = performer.perform_action(
                        url=step.url,
                        action=step.action,
                        selector=step.selector,
                        input_value=step.input_value,
                        wait_time=step.wait_time,
                        session_id=session_id,
                        selector_type=step.selector_type,
                        verify_ssl=step.verify_ssl
                    )[0]
                    
                    action_results.append(step_result)
                    
                    # Update state validation
                    if step_result["success"]:
                        sequence.state_checks[i] = {
                            "url": step_result["page_url"],
                            "title": step_result["page_title"]
                        }
                
                result["results"] = action_results
                result["success"] = all(r["success"] for r in action_results)
                
            elif action == "delete":
                if session_id and session_id in _SESSIONS:
                    sequences = _SESSIONS[session_id].action_sequences
                    if sequences and sequence_name in sequences:
                        del sequences[sequence_name]
                        _save_sessions()
                        result["success"] = True
                    else:
                        result["error"] = f"Sequence {sequence_name} not found"
                else:
                    result["error"] = "Invalid session_id"
                    
            elif action == "list":
                if session_id and session_id in _SESSIONS:
                    sequences = _SESSIONS[session_id].action_sequences or {}
                    result["sequences"] = {
                        name: asdict(seq) for name, seq in sequences.items()
                    }
                    result["success"] = True
                else:
                    result["sequences"] = {}
                    result["success"] = True
            
        except json.JSONDecodeError:
            result["error"] = "Invalid steps JSON format"
        except ValueError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = "An unexpected error occurred"
        
        return (result,)

class WebActionPerformer:
    # Rate limiting
    _RATE_LIMIT = 10  # requests per minute
    _request_times = []
    _rate_limit_lock = threading.Lock()
    """Web page action performer API endpoint."""
    
    CATEGORY = "web_access"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for web action performer."""
        return {
            "required": {
                "url": ("STRING", {
                    "multiline": False,
                    "placeholder": "https://example.com"
                }),
                "action": (["click", "input", "submit", "wait", "navigate"],
                          {"default": "click"}),
                "selector": ("STRING", {
                    "multiline": False,
                    "placeholder": "CSS selector or XPath"
                }),
            },
            "optional": {
                "input_value": ("STRING", {
                    "multiline": True,
                    "placeholder": "Value to input into form field"
                }),
                "wait_time": ("INTEGER", {
                    "default": 5,
                    "min": 1,
                    "max": 60
                }),
                "session_id": ("STRING", {
                    "multiline": False,
                    "placeholder": "Session ID for maintaining state"
                }),
                "selector_type": (["css", "xpath", "id", "name", "class"],
                                {"default": "css"})
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("action_result",)
    FUNCTION = "perform_action"
    
    def _get_by_method(self, selector_type: str) -> By:
        """Get the Selenium By method for the selector type."""
        return {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME
        }.get(selector_type, By.CSS_SELECTOR)
    
    def _check_rate_limit(self):
        """Check if we're within rate limits."""
        now = time.time()
        minute_ago = now - 60
        
        with self._rate_limit_lock:
            # Clean old requests
            self._request_times = [t for t in self._request_times if t > minute_ago]
            
            # Check limit
            if len(self._request_times) >= self._RATE_LIMIT:
                raise ValueError("Rate limit exceeded")
            
            # Add current request
            self._request_times.append(now)
    
    def perform_action(self, url: str, action: str, selector: str,
                      input_value: Optional[str] = None,
                      wait_time: int = 5,
                      session_id: Optional[str] = None,
                      selector_type: str = "css",
                      verify_ssl: bool = True) -> Tuple[Dict]:
        """
        Perform an action on a web page.
        
        Args:
            url: The URL to perform the action on
            action: The type of action to perform
            selector: Element selector
            input_value: Value to input (for input action)
            wait_time: Time to wait for element/page load
            session_id: Session ID for maintaining state
            selector_type: Type of selector to use
            
        Returns:
            Dictionary containing action result
        """
        result = {
            "url": url,
            "action": action,
            "selector": selector,
            "timestamp": time.time(),
            "success": False,
            "error": None
        }
        
        try:
            # Validate URL
            if not _validate_url(url):
                raise ValueError("Invalid URL format or scheme")
            
            # Check rate limit
            self._check_rate_limit()
            
            driver = None
            try:
                driver = self._create_selenium_driver()
                driver.set_page_load_timeout(wait_time)
                driver.get(url)
                by_method = self._get_by_method(selector_type)
                
                # Wait for element to be present
                element = WebDriverWait(driver, wait_time).until(
                    EC.presence_of_element_located((by_method, selector))
                )
                
                if action == "click":
                    element.click()
                elif action == "input" and input_value is not None:
                    element.clear()
                    element.send_keys(input_value)
                elif action == "submit":
                    element.submit()
                elif action == "wait":
                    time.sleep(wait_time)
                
                # Capture the page state after action
                result["page_url"] = driver.current_url
                result["page_title"] = driver.title
                
                # Take screenshot of the result
                screenshot = driver.get_screenshot_as_base64()
                result["screenshot"] = screenshot
                
                result["success"] = True
                
            except TimeoutException:
                result["error"] = f"Element not found within {wait_time} seconds"
            except NoSuchElementException:
                result["error"] = f"Element not found: {selector}"
            except Exception as e:
                result["error"] = "An unexpected error occurred"
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass  # Ignore errors during cleanup
                
        except ValueError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = "An unexpected error occurred"
        
        return (result,)
    
    def _create_selenium_driver(self):
        """Create a new Selenium WebDriver instance with security options."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--user-agent=Createve.AI API Client/1.0')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

# Module exports
NODE_CLASS_MAPPINGS = {
    "webInfoRetriever": WebInfoRetriever,
    "webActionPerformer": WebActionPerformer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "webInfoRetriever": "Web Info Retriever",
    "webActionPerformer": "Web Action Performer"
}

API_SERVER_QUEUE_MODE = {
    WebInfoRetriever: True,  # Queue mode for potentially slow operations
    WebActionPerformer: True  # Queue mode for web automation
}
