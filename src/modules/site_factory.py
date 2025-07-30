"""
Factory for creating and managing site modules with dynamic registration.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Union
from dataclasses import dataclass
from datetime import datetime

from src.modules.base_site_module import BaseSiteModule
from src.models.site_config import SiteConfig
from src.utils.logger import logger
from src.utils.exceptions import ConfigurationError


@dataclass
class ModuleInfo:
    """Information about a registered site module."""
    
    name: str
    module_class: Type[BaseSiteModule]
    description: str
    version: str
    supported_domains: List[str]
    requires_auth: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'class_name': self.module_class.__name__,
            'description': self.description,
            'version': self.version,
            'supported_domains': self.supported_domains,
            'requires_auth': self.requires_auth,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count
        }


class SiteModuleRegistry:
    """Registry for managing site modules."""
    
    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._domain_mapping: Dict[str, str] = {}
        logger.info("SiteModuleRegistry initialized")
    
    def register_module(self, 
                       name: str,
                       module_class: Type[BaseSiteModule],
                       description: str = "",
                       version: str = "1.0",
                       supported_domains: Optional[List[str]] = None) -> None:
        """Register a new site module."""
        if not issubclass(module_class, BaseSiteModule):
            raise ConfigurationError(
                f"Module class must inherit from BaseSiteModule",
                config_key=name
            )
        
        if name in self._modules:
            logger.warning(f"Module '{name}' already registered, overwriting")
        
        supported_domains = supported_domains or []
        
        module_info = ModuleInfo(
            name=name,
            module_class=module_class,
            description=description,
            version=version,
            supported_domains=supported_domains,
            requires_auth=self._check_auth_requirement(module_class),
            created_at=datetime.now()
        )
        
        self._modules[name] = module_info
        
        for domain in supported_domains:
            self._domain_mapping[domain.lower()] = name
        
        logger.info(f"Registered module: {name} (domains: {supported_domains})")
    
    def unregister_module(self, name: str) -> bool:
        """Unregister a site module."""
        if name not in self._modules:
            return False
        
        module_info = self._modules[name]
        
        for domain in module_info.supported_domains:
            self._domain_mapping.pop(domain.lower(), None)
        
        del self._modules[name]
        
        logger.info(f"Unregistered module: {name}")
        return True
    
    def get_module_by_name(self, name: str) -> Optional[ModuleInfo]:
        """Get module info by name."""
        return self._modules.get(name)
    
    def get_module_by_domain(self, domain: str) -> Optional[ModuleInfo]:
        """Get module info by domain."""
        module_name = self._domain_mapping.get(domain.lower())
        return self._modules.get(module_name) if module_name else None
    
    def list_modules(self) -> Dict[str, ModuleInfo]:
        """List all registered modules."""
        return self._modules.copy()
    
    def get_modules_by_capability(self, capability: str) -> List[ModuleInfo]:
        """Get modules that support a specific capability."""
        modules = []
        
        for module_info in self._modules.values():
            if hasattr(module_info.module_class, f'supports_{capability}'):
                method = getattr(module_info.module_class, f'supports_{capability}')
                if callable(method) and method():
                    modules.append(module_info)
        
        return modules
    
    def _check_auth_requirement(self, module_class: Type[BaseSiteModule]) -> bool:
        """Check if module requires authentication."""
        auth_method = getattr(module_class, '_perform_authentication', None)
        if auth_method:
            source = inspect.getsource(auth_method)
            return 'return True' not in source or 'pass' not in source
        return False
    
    def update_usage_stats(self, name: str) -> None:
        """Update usage statistics for a module."""
        if name in self._modules:
            self._modules[name].last_used = datetime.now()
            self._modules[name].usage_count += 1


class SiteFactory:
    """Factory for creating site modules."""
    
    def __init__(self):
        self.registry = SiteModuleRegistry()
        self._auto_discover_modules()
        logger.info("SiteFactory initialized")
    
    def create_module(self, 
                     site_config: SiteConfig,
                     module_name: Optional[str] = None) -> BaseSiteModule:
        """Create a site module instance."""
        try:
            if module_name:
                module_info = self.registry.get_module_by_name(module_name)
                if not module_info:
                    raise ConfigurationError(f"Module not found: {module_name}")
            else:
                domain = self._extract_domain(site_config.base_url)
                module_info = self.registry.get_module_by_domain(domain)
                
                if not module_info:
                    logger.info(f"No specific module found for domain: {domain}, using generic module")
                    return self._create_generic_module(site_config)
            
            module_instance = module_info.module_class(site_config)
            
            self.registry.update_usage_stats(module_info.name)
            
            logger.info(f"Created module instance: {module_info.name}")
            return module_instance
            
        except Exception as e:
            logger.error(f"Failed to create module: {e}")
            raise ConfigurationError(f"Module creation failed: {e}")
    
    def register_module_from_file(self, file_path: Union[str, Path]) -> None:
        """Register a module from a Python file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Module file not found: {file_path}")
        
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseSiteModule) and 
                    obj != BaseSiteModule):
                    
                    module_name = getattr(obj, 'MODULE_NAME', name)
                    description = getattr(obj, 'MODULE_DESCRIPTION', f"Auto-discovered module from {file_path.name}")
                    version = getattr(obj, 'MODULE_VERSION', "1.0")
                    domains = getattr(obj, 'SUPPORTED_DOMAINS', [])
                    
                    self.registry.register_module(
                        name=module_name,
                        module_class=obj,
                        description=description,
                        version=version,
                        supported_domains=domains
                    )
                    
                    logger.info(f"Auto-registered module from file: {file_path}")
                    break
            
        except Exception as e:
            logger.error(f"Failed to register module from {file_path}: {e}")
            raise ConfigurationError(f"Module registration failed: {e}")
    
    def _auto_discover_modules(self) -> None:
        """Auto-discover modules in the sites directory."""
        sites_dir = Path(__file__).parent / 'sites'
        
        if not sites_dir.exists():
            logger.warning("Sites directory not found, creating it")
            sites_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for module_file in sites_dir.glob('*_module.py'):
            try:
                self.register_module_from_file(module_file)
            except Exception as e:
                logger.warning(f"Failed to auto-discover module {module_file}: {e}")
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _create_generic_module(self, site_config: SiteConfig) -> BaseSiteModule:
        """Create a generic module for sites without specific implementations."""
        from src.modules.sites.generic_module import GenericSiteModule
        return GenericSiteModule(site_config)
    
    def validate_module_config(self, module_name: str, site_config: SiteConfig) -> Dict[str, Any]:
        """Validate if a module can work with the given site config."""
        module_info = self.registry.get_module_by_name(module_name)
        
        if not module_info:
            return {
                'valid': False,
                'issues': [f"Module '{module_name}' not found"],
                'recommendations': ['Check module name and ensure it is registered']
            }
        
        issues = []
        recommendations = []
        
        domain = self._extract_domain(site_config.base_url)
        if (module_info.supported_domains and 
            domain not in module_info.supported_domains):
            issues.append(f"Domain '{domain}' not in supported domains: {module_info.supported_domains}")
            recommendations.append("Consider using a different module or add domain support")
        
        if module_info.requires_auth and not site_config.auth_config.required:
            issues.append("Module requires authentication but site config doesn't specify auth")
            recommendations.append("Configure authentication in site config")
        
        config_issues = site_config.validate()
        if config_issues:
            issues.extend(config_issues)
            recommendations.append("Fix site configuration issues")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations,
            'module_info': module_info.to_dict()
        }
    
    def get_recommended_modules(self, site_config: SiteConfig) -> List[Dict[str, Any]]:
        """Get recommended modules for a site config."""
        domain = self._extract_domain(site_config.base_url)
        recommendations = []
        
        for module_info in self.registry.list_modules().values():
            if domain in module_info.supported_domains:
                score = 1.0  
            else:
                score = 0.5  
            
            if module_info.requires_auth == site_config.auth_config.required:
                score += 0.2
            
            if module_info.usage_count > 0:
                score += 0.1
            
            recommendations.append({
                'module_name': module_info.name,
                'score': score,
                'reason': self._get_recommendation_reason(module_info, site_config),
                'module_info': module_info.to_dict()
            })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:3]  
    
    def _get_recommendation_reason(self, module_info: ModuleInfo, site_config: SiteConfig) -> str:
        """Get reason for module recommendation."""
        domain = self._extract_domain(site_config.base_url)
        
        if domain in module_info.supported_domains:
            return f"Specifically designed for {domain}"
        
        if module_info.requires_auth == site_config.auth_config.required:
            return "Authentication requirements match"
        
        if module_info.usage_count > 10:
            return "Popular and well-tested module"
        
        return "General compatibility"
    
    def export_module_registry(self) -> Dict[str, Any]:
        """Export the module registry for backup or analysis."""
        return {
            'modules': {name: info.to_dict() for name, info in self.registry.list_modules().items()},
            'domain_mapping': self.registry._domain_mapping,
            'exported_at': datetime.now().isoformat()
        }
    
    def import_module_registry(self, registry_data: Dict[str, Any]) -> None:
        """Import module registry from backup data."""
        logger.warning("Registry import not fully implemented - requires module class loading")
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """Get factory usage statistics."""
        modules = self.registry.list_modules()
        
        return {
            'total_modules': len(modules),
            'modules_with_auth': sum(1 for m in modules.values() if m.requires_auth),
            'total_usage': sum(m.usage_count for m in modules.values()),
            'most_used_module': max(modules.items(), key=lambda x: x[1].usage_count)[0] if modules else None,
            'supported_domains': len(set().union(*[m.supported_domains for m in modules.values()])),
            'registry_created_at': min(m.created_at for m in modules.values()) if modules else None
        }


factory = SiteFactory()