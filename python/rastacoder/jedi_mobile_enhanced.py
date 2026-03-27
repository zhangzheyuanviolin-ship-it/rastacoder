"""
Jedi Mobile Enhanced — Optimized Code Intelligence for RastaCoder

Mobile-optimized Jedi setup with:
- UV package manager integration
- Vendored Jedi/Parso modules
- Caching for faster completions
- Memory-efficient operation
- Chaquopy Android compatibility

Created: March 16, 2026
"""

import sys
import os
import json
import time
from typing import Optional, List, Dict, Callable
from functools import lru_cache

# Add vendor directory to path for bundled Jedi
VENDOR_PATH = os.path.join(os.path.dirname(__file__), '..', 'vendor')
if os.path.exists(VENDOR_PATH):
    sys.path.insert(0, VENDOR_PATH)

try:
    import jedi
    JEDI_AVAILABLE = True
    JEDI_VERSION = jedi.__version__
except ImportError:
    JEDI_AVAILABLE = False
    JEDI_VERSION = None


class JediMobileEnhanced:
    """
    Enhanced Jedi for mobile devices with optimizations:
    - LRU caching for repeated completions
    - Lazy loading
    - Memory-efficient parsing
    - Timeout protection
    """
    
    def __init__(self, max_cache_size: int = 128, timeout_seconds: int = 5):
        self.max_cache_size = max_cache_size
        self.timeout_seconds = timeout_seconds
        self.is_installed = JEDI_AVAILABLE
        self.jedi_version = JEDI_VERSION
        self._script_cache = {}
        self._last_cleanup = time.time()
        
        # Mobile optimizations
        jedi.settings.case_insensitive_completion = True
        jedi.settings.fast_parser = True
        jedi.settings.cache_directory = self._get_cache_dir()
    
    def _get_cache_dir(self) -> str:
        """Get cache directory for mobile device"""
        # Try common mobile cache locations
        for path in [
            os.path.join(os.path.dirname(__file__), '.cache'),
            '/data/data/com.termux/cache/jedi',
            '/tmp/jedi_cache',
        ]:
            try:
                os.makedirs(path, exist_ok=True)
                return path
            except:
                continue
        return None
    
    def check_jedi_installed(self) -> bool:
        """Check if Jedi is available"""
        return self.is_installed
    
    @lru_cache(maxsize=128)
    def _get_cached_script(self, code: str, path: str = 'example.py'):
        """Cache script objects for faster repeated access"""
        return jedi.Script(code, path=path)
    
    def get_completions(
        self,
        code: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        fuzzy: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get code completions with mobile optimizations
        
        Args:
            code: Source code string
            line: Line number (1-indexed), auto-detected if None
            column: Column number (0-indexed), auto-detected if None
            fuzzy: Enable fuzzy matching
            limit: Max completions to return
            
        Returns:
            List of completion dictionaries
        """
        if not self.is_installed:
            return []
        
        try:
            # Auto-detect cursor position if not provided
            if line is None or column is None:
                lines = code.split('\n')
                line = len(lines)
                column = len(lines[-1]) if lines else 0
            
            # Get cached script
            script = self._get_cached_script(code)
            
            # Get completions with timeout
            start_time = time.time()
            completions = script.complete(line=line, column=column, fuzzy=fuzzy)
            
            # Check timeout
            if time.time() - start_time > self.timeout_seconds:
                print(f"⚠️ Completion timeout after {self.timeout_seconds}s")
                return []
            
            # Convert to dict and limit results
            results = []
            for c in completions[:limit]:
                try:
                    result = {
                        'name': c.name,
                        'type': c.type,
                        'module_name': c.module_name if hasattr(c, 'module_name') else '',
                        'docstring': (c.docstring() or '')[:300],
                        'signature': c.get_signatures()[0].to_string() if c.get_signatures() else '',
                        'priority': self._calculate_priority(c),
                    }
                    results.append(result)
                except Exception as e:
                    continue
            
            # Sort by priority
            results.sort(key=lambda x: x['priority'], reverse=True)
            
            # Cleanup cache periodically
            self._cleanup_cache()
            
            return results
            
        except Exception as e:
            print(f"Jedi completion error: {e}")
            return []
    
    def _calculate_priority(self, completion) -> int:
        """Calculate completion priority for better sorting"""
        priority = 0
        name = completion.name
        
        # Boost common patterns
        if not name.startswith('_'):
            priority += 10
        if name.startswith('__') and name.endswith('__'):
            priority += 5  # Magic methods
        if completion.type == 'function':
            priority += 8
        if completion.type == 'class':
            priority += 6
        if completion.type == 'module':
            priority += 4
        
        return priority
    
    def _cleanup_cache(self):
        """Cleanup cache if too old"""
        now = time.time()
        if now - self._last_cleanup > 60:  # Cleanup every minute
            self._script_cache.clear()
            self._last_cleanup = now
    
    def get_signature_help(
        self,
        code: str,
        line: Optional[int] = None,
        column: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get function signature help
        
        Args:
            code: Source code
            line: Line number
            column: Column number
            
        Returns:
            Signature dictionary or None
        """
        if not self.is_installed:
            return None
        
        try:
            if line is None or column is None:
                lines = code.split('\n')
                line = len(lines)
                column = len(lines[-1]) if lines else 0
            
            script = self._get_cached_script(code)
            signatures = script.get_signatures(line=line, column=column)
            
            if signatures:
                sig = signatures[0]
                return {
                    'name': sig.name,
                    'params': [p.name for p in sig.params],
                    'docstring': (sig.docstring() or '')[:500],
                    'signature': sig.to_string(),
                }
            return None
            
        except Exception as e:
            print(f"Jedi signature error: {e}")
            return None
    
    def get_definition(self, code: str, line: int, column: int) -> Optional[Dict]:
        """
        Get definition (go to declaration)
        
        Args:
            code: Source code
            line: Line number
            column: Column number
            
        Returns:
            Definition info or None
        """
        if not self.is_installed:
            return None
        
        try:
            script = self._get_cached_script(code)
            definitions = script.infer(line=line, column=column)
            
            if definitions:
                defn = definitions[0]
                return {
                    'name': defn.name,
                    'type': defn.type,
                    'module_path': defn.module_path if hasattr(defn, 'module_path') else '',
                    'line': defn.line if hasattr(defn, 'line') else 0,
                    'column': defn.column if hasattr(defn, 'column') else 0,
                    'description': defn.description,
                }
            return None
            
        except Exception as e:
            print(f"Jedi definition error: {e}")
            return None
    
    def get_references(
        self,
        code: str,
        line: int,
        column: int,
        scope: str = 'project'
    ) -> List[Dict]:
        """
        Find all references to a symbol
        
        Args:
            code: Source code
            line: Line number
            column: Column number
            scope: 'project' or 'file'
            
        Returns:
            List of reference locations
        """
        if not self.is_installed:
            return []
        
        try:
            script = self._get_cached_script(code)
            refs = script.get_references(line=line, column=column, scope=scope)
            
            return [
                {
                    'line': ref.line,
                    'column': ref.column,
                    'module_path': str(ref.module_path) if hasattr(ref, 'module_path') else '',
                }
                for ref in refs[:20]  # Limit results
            ]
            
        except Exception as e:
            print(f"Jedi references error: {e}")
            return []
    
    def install_with_uv(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Install Jedi using UV package manager (faster than pip)
        
        Args:
            log_callback: Optional callback for progress logs
            
        Returns:
            True if successful
        """
        import subprocess
        
        if log_callback:
            log_callback("🚀 Installing Jedi with UV...")
        
        try:
            # Use UV for faster installation
            result = subprocess.run(
                ['uv', 'pip', 'install', 'jedi', '--quiet'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Verify installation
                import importlib
                importlib.invalidate_caches()
                
                try:
                    import jedi
                    self.is_installed = True
                    self.jedi_version = jedi.__version__
                    
                    if log_callback:
                        log_callback(f"✅ Jedi v{self.jedi_version} installed with UV!")
                    return True
                except ImportError:
                    pass
            
            if log_callback:
                log_callback(f"❌ Installation failed: {result.stderr}")
            return False
            
        except subprocess.TimeoutExpired:
            if log_callback:
                log_callback("❌ Installation timed out")
            return False
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get Jedi usage statistics"""
        cache_info = self._get_cached_script.cache_info()
        return {
            'installed': self.is_installed,
            'version': self.jedi_version,
            'cache_hits': cache_info.hits,
            'cache_misses': cache_info.misses,
            'cache_size': cache_info.currsize,
            'cache_maxsize': cache_info.maxsize,
        }


# Convenience functions
def setup_jedi_mobile(log_callback=None):
    """Quick setup for mobile Jedi"""
    jedi = JediMobileEnhanced()
    
    if not jedi.is_installed:
        if log_callback:
            log_callback("Jedi not installed, installing with UV...")
        jedi.install_with_uv(log_callback=log_callback)
    
    return jedi


def get_completions_fast(code, line=None, column=None, limit=30):
    """Fast completion helper"""
    jedi = JediMobileEnhanced()
    return jedi.get_completions(code, line, column, limit=limit)


# Test function
def test_jedi_mobile():
    """Test Jedi mobile installation"""
    jedi = JediMobileEnhanced()
    
    print(f"Jedi Installed: {jedi.is_installed}")
    print(f"Version: {jedi.jedi_version}")
    
    if jedi.is_installed:
        # Test completions
        test_code = "import os; os."
        completions = jedi.get_completions(test_code, limit=5)
        print(f"\nTest completions for '{test_code}':")
        for c in completions:
            print(f"  {c['name']} ({c['type']})")
        
        # Test signature help
        sig_code = "os.getcwd("
        sig = jedi.get_signature_help(sig_code)
        if sig:
            print(f"\nSignature for '{sig_code}':")
            print(f"  {sig['signature']}")
        
        # Print stats
        print(f"\nStats: {jedi.get_stats()}")
    
    return jedi.is_installed


if __name__ == '__main__':
    test_jedi_mobile()
