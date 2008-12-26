# Copyright 2008 Kaspars Dancis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



from datetime import datetime

def escape(text):
    
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')



def from_iso(s):
    dt = datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    try: dt = dt.replace(microsecond = int(s[20:]))
    except: pass
    return dt

def to_iso(dt):
    return dt.isoformat()



class Log:
    def __init__(self, f):
        self.f = f
        
    def write(self, s):
        self.f.write(s)
        self.f.flush()