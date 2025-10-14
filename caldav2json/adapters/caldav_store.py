
import requests
from caldav import DAVClient, Calendar
from typing import List

class RadicaleCalendarStore:
    def __init__(self, calendar_url: str, username: str | None, password: str | None, verify_ssl: bool = True):
        self.calendar_url = calendar_url.rstrip("/") + "/"
        self.username = username
        self.password = password
        self.verify = verify_ssl
        self.client = DAVClient(url=self.calendar_url, username=username, password=password)
        self.cal = Calendar(client=self.client, url=self.calendar_url)

    def list_objects(self) -> List[bytes]:
        out: List[bytes] = []
        for obj in self.cal.objects():
            data = getattr(obj, "data", None)
            if data is None:
                try:
                    data = obj._get_data()
                except Exception:
                    data = None
            if data is None:
                continue
            if isinstance(data, str):
                data = data.encode("utf-8", errors="replace")
            out.append(data)
        return out

    def list_todos(self) -> List[bytes]:
        try:
            it = self.cal.todos()
        except Exception:
            return []
        out: List[bytes] = []
        for obj in it:
            data = getattr(obj, "data", None)
            if data is None:
                try:
                    data = obj._get_data()
                except Exception:
                    data = None
            if data is None:
                continue
            if isinstance(data, str):
                data = data.encode("utf-8", errors="replace")
            out.append(data)
        return out

    def put_vtodo(self, todo_ics: bytes, uid: str) -> str:
        put_url = f"{self.calendar_url}{uid}.ics"
        resp = requests.put(
            put_url,
            data=todo_ics,
            auth=(self.username, self.password) if self.username or self.password else None,
            headers={"Content-Type": "text/calendar; charset=utf-8"},
            verify=self.verify,
            timeout=30,
        )
        resp.raise_for_status()
        return put_url

    # --- DIAGNOSTICS: raw WebDAV listing & fetch (no behavior change) ---
    def debug_list_resource_hrefs(self) -> list[str]:
        """
        PROPFIND Depth:1 to list all child resources. Returns absolute URLs of .ics files.
        """
        import xml.etree.ElementTree as ET
        from urllib.parse import urljoin

        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<d:propfind xmlns:d="DAV:">'
            '<d:prop><d:getcontentlength/><d:getetag/><d:resourcetype/></d:prop>'
            '</d:propfind>'
        )
        try:
            resp = requests.request(
                "PROPFIND",
                self.calendar_url,
                data=body.encode("utf-8"),
                headers={"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
                auth=(self.username, self.password) if self.username or self.password else None,
                verify=self.verify,
                timeout=30,
            )
            print(f"[webdav] PROPFIND {self.calendar_url} -> {resp.status_code}")
            resp.raise_for_status()
        except Exception as e:
            print(f"[webdav] PROPFIND ERROR: {e}")
            return []

        hrefs: list[str] = []
        try:
            ns = {"d": "DAV:"}
            root = ET.fromstring(resp.content)
            for resp_el in root.findall("d:response", ns):
                href_el = resp_el.find("d:href", ns)
                if href_el is None or not href_el.text:
                    continue
                href_abs = urljoin(self.calendar_url, href_el.text)
                if href_abs.endswith(".ics"):
                    hrefs.append(href_abs)
            print(f"[webdav] resources: {len(hrefs)} .ics")
        except Exception as e:
            print(f"[webdav] PARSE ERROR: {e}")

        return hrefs

    def debug_get_ics(self, url: str) -> bytes | None:
        """
        Raw GET of a resource. Returns bytes or None on error.
        """
        try:
            r = requests.get(
                url,
                auth=(self.username, self.password) if self.username or self.password else None,
                verify=self.verify,
                timeout=30,
            )
            print(f"[webdav] GET {url} -> {r.status_code} size={len(r.content) if r.ok else 0}")
            r.raise_for_status()
            return r.content
        except Exception as e:
            print(f"[webdav] GET ERROR {url}: {e}")
            return None
