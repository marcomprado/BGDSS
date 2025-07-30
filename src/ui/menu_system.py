"""
MenuSystem - Sistema de Menus Dinâmicos para Terminal

FUNCIONALIDADE:
    Sistema avançado de menus interativos para terminal com navegação por teclado,
    validação de inputs, menus hierárquicos e interface responsiva. Fornece
    experiência de usuário rica e intuitiva para aplicações de terminal.

RESPONSABILIDADES:
    - Criação e gerenciamento de menus dinâmicos e hierárquicos
    - Navegação por teclado (setas, enter, esc, tab)
    - Validação automática de inputs com feedback imediato
    - Renderização responsiva e otimizada para terminal
    - Suporte a diferentes tipos de inputs (texto, numérico, seleção)

INTEGRAÇÃO NO SISTEMA:
    - Base para todas as interfaces de usuário do terminal
    - Usado por interactive_mode.py e terminal_interface.py
    - Integra com sistema de logging para feedback
    - Suporte a themes e personalização visual

PADRÕES DE DESIGN:
    - Command Pattern: Ações de menu como comandos
    - State Pattern: Estados de navegação e input
    - Builder Pattern: Construção de menus complexos
    - Observer Pattern: Eventos de navegação

CARACTERÍSTICAS TÉCNICAS:
    - Detecção automática de tamanho do terminal
    - Scroll automático para menus grandes
    - Highlighting e seleção visual
    - Suporte a ícones e cores
    - Validação em tempo real
"""

import sys
import os
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json

try:
    import keyboard
    import colorama
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    ADVANCED_INPUT = True
except ImportError:
    ADVANCED_INPUT = False
    # Fallback colors for systems without colorama
    class Fore:
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'
        RESET = '\033[0m'
    
    class Back:
        BLACK = '\033[40m'
        RED = '\033[41m'
        GREEN = '\033[42m'
        YELLOW = '\033[43m'
        BLUE = '\033[44m'
        MAGENTA = '\033[45m'
        CYAN = '\033[46m'
        WHITE = '\033[47m'
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        NORMAL = '\033[22m'
        RESET_ALL = '\033[0m'

from src.utils.logger import logger


class MenuItemType(Enum):
    """Tipos de itens de menu disponíveis."""
    ACTION = "action"           # Executa uma ação
    SUBMENU = "submenu"        # Abre submenu
    INPUT = "input"            # Solicita input do usuário
    TOGGLE = "toggle"          # Toggle on/off
    SEPARATOR = "separator"    # Separador visual
    BACK = "back"              # Volta ao menu anterior
    EXIT = "exit"              # Sai da aplicação


class InputType(Enum):
    """Tipos de input suportados."""
    TEXT = "text"
    NUMBER = "number"
    FLOAT = "float"
    EMAIL = "email"
    URL = "url"
    PATH = "path"
    PASSWORD = "password"
    CHOICE = "choice"
    MULTI_CHOICE = "multi_choice"
    CONFIRMATION = "confirmation"


class MenuTheme(Enum):
    """Temas visuais disponíveis."""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    COLORFUL = "colorful"
    MINIMAL = "minimal"


@dataclass
class MenuStyle:
    """Configuração de estilo para menus."""
    border_char: str = "━"
    corner_char: str = "┏┓┗┛"
    selection_bg: str = Back.BLUE
    selection_fg: str = Fore.WHITE
    title_fg: str = Fore.CYAN
    subtitle_fg: str = Fore.YELLOW
    text_fg: str = Fore.WHITE
    accent_fg: str = Fore.GREEN
    error_fg: str = Fore.RED
    warning_fg: str = Fore.YELLOW
    success_fg: str = Fore.GREEN
    icons: Dict[str, str] = field(default_factory=lambda: {
        'arrow': '▶',
        'selected': '●',
        'unselected': '○',
        'submenu': '▶',
        'back': '◀',
        'exit': '✕',
        'action': '⚡',
        'input': '✎',
        'toggle_on': '✓',
        'toggle_off': '✗',
        'separator': '─'
    })


@dataclass
class ValidationRule:
    """Regra de validação para inputs."""
    validator: Callable[[str], bool]
    error_message: str
    warning_message: Optional[str] = None


@dataclass
class MenuItem:
    """Item individual de menu."""
    key: str
    title: str
    item_type: MenuItemType
    description: Optional[str] = None
    action: Optional[Callable] = None
    submenu: Optional['Menu'] = None
    input_type: Optional[InputType] = None
    validation_rules: List[ValidationRule] = field(default_factory=list)
    default_value: Any = None
    choices: Optional[List[str]] = None
    enabled: bool = True
    visible: bool = True
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Menu:
    """
    Classe principal para criação e gerenciamento de menus.
    
    Suporta menus hierárquicos, navegação por teclado e validação de inputs.
    """
    
    def __init__(self, 
                 title: str, 
                 subtitle: Optional[str] = None,
                 style: Optional[MenuStyle] = None,
                 max_visible_items: int = 10):
        self.title = title
        self.subtitle = subtitle
        self.style = style or MenuStyle()
        self.max_visible_items = max_visible_items
        self.items: List[MenuItem] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.parent_menu: Optional['Menu'] = None
        self.result_data: Dict[str, Any] = {}
        self.running = False
        
    def add_item(self, item: MenuItem) -> 'Menu':
        """Adiciona item ao menu."""
        self.items.append(item)
        if item.submenu:
            item.submenu.parent_menu = self
        return self
    
    def add_action(self, key: str, title: str, action: Callable, 
                   description: str = None, icon: str = None) -> 'Menu':
        """Adiciona item de ação ao menu."""
        item = MenuItem(
            key=key,
            title=title,
            item_type=MenuItemType.ACTION,
            description=description,
            action=action,
            icon=icon
        )
        return self.add_item(item)
    
    def add_submenu(self, key: str, title: str, submenu: 'Menu',
                    description: str = None, icon: str = None) -> 'Menu':
        """Adiciona submenu."""
        item = MenuItem(
            key=key,
            title=title,
            item_type=MenuItemType.SUBMENU,
            description=description,
            submenu=submenu,
            icon=icon
        )
        return self.add_item(item)
    
    def add_input(self, key: str, title: str, input_type: InputType,
                  description: str = None, validation_rules: List[ValidationRule] = None,
                  default_value: Any = None, choices: List[str] = None) -> 'Menu':
        """Adiciona item de input."""
        item = MenuItem(
            key=key,
            title=title,
            item_type=MenuItemType.INPUT,
            description=description,
            input_type=input_type,
            validation_rules=validation_rules or [],
            default_value=default_value,
            choices=choices
        )
        return self.add_item(item)
    
    def add_toggle(self, key: str, title: str, default_value: bool = False,
                   description: str = None) -> 'Menu':
        """Adiciona toggle switch."""
        item = MenuItem(
            key=key,
            title=title,
            item_type=MenuItemType.TOGGLE,
            description=description,
            default_value=default_value
        )
        return self.add_item(item)
    
    def add_separator(self, title: str = "") -> 'Menu':
        """Adiciona separador visual."""
        item = MenuItem(
            key=f"sep_{len(self.items)}",
            title=title,
            item_type=MenuItemType.SEPARATOR,
            enabled=False
        )
        return self.add_item(item)
    
    def add_back(self, title: str = "← Voltar") -> 'Menu':
        """Adiciona opção de voltar."""
        item = MenuItem(
            key="back",
            title=title,
            item_type=MenuItemType.BACK,
            icon=self.style.icons['back']
        )
        return self.add_item(item)
    
    def add_exit(self, title: str = "✕ Sair") -> 'Menu':
        """Adiciona opção de sair."""
        item = MenuItem(
            key="exit",
            title=title,
            item_type=MenuItemType.EXIT,
            icon=self.style.icons['exit']
        )
        return self.add_item(item)


class MenuRenderer:
    """Renderizador responsável pela exibição visual dos menus."""
    
    def __init__(self, style: MenuStyle):
        self.style = style
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
    
    def _get_terminal_width(self) -> int:
        """Obtém largura do terminal."""
        try:
            return os.get_terminal_size().columns
        except:
            return 80
    
    def _get_terminal_height(self) -> int:
        """Obtém altura do terminal."""
        try:
            return os.get_terminal_size().lines
        except:
            return 24
    
    def clear_screen(self):
        """Limpa a tela."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def render_menu(self, menu: Menu):
        """Renderiza menu completo."""
        self.clear_screen()
        
        # Header
        self._render_header(menu)
        
        # Menu items
        self._render_items(menu)
        
        # Footer
        self._render_footer(menu)
        
        # Status line
        self._render_status_line(menu)
    
    def _render_header(self, menu: Menu):
        """Renderiza cabeçalho do menu."""
        # Title
        title_line = f" {menu.title} "
        title_centered = title_line.center(self.terminal_width, self.style.border_char)
        print(f"{self.style.title_fg}{Style.BRIGHT}{title_centered}{Style.RESET_ALL}")
        
        # Subtitle
        if menu.subtitle:
            subtitle_line = f"{menu.subtitle}"
            subtitle_centered = subtitle_line.center(self.terminal_width)
            print(f"{self.style.subtitle_fg}{subtitle_centered}{Style.RESET_ALL}")
            print()
    
    def _render_items(self, menu: Menu):
        """Renderiza itens do menu."""
        visible_items = [item for item in menu.items if item.visible]
        
        # Calculate visible range
        start_idx = menu.scroll_offset
        end_idx = min(start_idx + menu.max_visible_items, len(visible_items))
        
        for i, item in enumerate(visible_items[start_idx:end_idx], start_idx):
            self._render_item(item, i == menu.selected_index, i + 1)
        
        # Scroll indicators
        if menu.scroll_offset > 0:
            print(f"{self.style.accent_fg}{'▲ Mais opções acima'.center(self.terminal_width)}{Style.RESET_ALL}")
        
        if end_idx < len(visible_items):
            print(f"{self.style.accent_fg}{'▼ Mais opções abaixo'.center(self.terminal_width)}{Style.RESET_ALL}")
    
    def _render_item(self, item: MenuItem, is_selected: bool, number: int):
        """Renderiza item individual."""
        if item.item_type == MenuItemType.SEPARATOR:
            separator = self.style.icons['separator'] * (self.terminal_width - 4)
            if item.title:
                separator = f" {item.title} ".center(self.terminal_width, self.style.icons['separator'])
            print(f"{self.style.text_fg}{separator}{Style.RESET_ALL}")
            return
        
        # Prefix
        prefix = f"{number:2d}. " if item.enabled else "    "
        
        # Icon
        icon = ""
        if item.icon:
            icon = f"{item.icon} "
        elif item.item_type == MenuItemType.ACTION:
            icon = f"{self.style.icons['action']} "
        elif item.item_type == MenuItemType.SUBMENU:
            icon = f"{self.style.icons['submenu']} "
        elif item.item_type == MenuItemType.INPUT:
            icon = f"{self.style.icons['input']} "
        elif item.item_type == MenuItemType.TOGGLE:
            toggle_icon = self.style.icons['toggle_on'] if item.default_value else self.style.icons['toggle_off']
            icon = f"{toggle_icon} "
        elif item.item_type == MenuItemType.BACK:
            icon = f"{self.style.icons['back']} "
        elif item.item_type == MenuItemType.EXIT:
            icon = f"{self.style.icons['exit']} "
        
        # Title and description
        title = item.title
        if item.description and len(title + item.description) < self.terminal_width - 20:
            title += f" - {item.description}"
        
        # Shortcut
        shortcut = ""
        if item.shortcut:
            shortcut = f" [{item.shortcut}]"
        
        # Selection highlighting
        if is_selected and item.enabled:
            line = f"{self.style.selection_bg}{self.style.selection_fg}"
            line += f"{prefix}{icon}{title}{shortcut}".ljust(self.terminal_width - 1)
            line += f"{Style.RESET_ALL}"
        else:
            color = self.style.text_fg if item.enabled else self.style.text_fg + Style.DIM
            line = f"{color}{prefix}{icon}{title}{shortcut}{Style.RESET_ALL}"
        
        print(line)
    
    def _render_footer(self, menu: Menu):
        """Renderiza rodapé com instruções."""
        print()
        instructions = []
        
        if ADVANCED_INPUT:
            instructions.extend([
                "↑↓ Navegar",
                "Enter Selecionar",
                "Esc Voltar"
            ])
        else:
            instructions.extend([
                "Digite o número da opção",
                "0 para voltar"
            ])
        
        instructions_text = " | ".join(instructions)
        instructions_centered = instructions_text.center(self.terminal_width)
        
        border = self.style.border_char * self.terminal_width
        print(f"{self.style.accent_fg}{border}{Style.RESET_ALL}")
        print(f"{self.style.text_fg}{instructions_centered}{Style.RESET_ALL}")
    
    def _render_status_line(self, menu: Menu):
        """Renderiza linha de status."""
        if menu.selected_index < len(menu.items):
            selected_item = menu.items[menu.selected_index]
            if selected_item.description:
                status = f" {selected_item.description} "
                status_line = status.center(self.terminal_width, '─')
                print(f"{self.style.subtitle_fg}{status_line}{Style.RESET_ALL}")


class InputValidator:
    """Validador de inputs com regras predefinidas."""
    
    @staticmethod
    def text(min_length: int = 0, max_length: int = 1000) -> ValidationRule:
        """Validação para texto."""
        def validate(value: str) -> bool:
            return min_length <= len(value.strip()) <= max_length
        
        return ValidationRule(
            validator=validate,
            error_message=f"Texto deve ter entre {min_length} e {max_length} caracteres"
        )
    
    @staticmethod
    def number(min_val: int = None, max_val: int = None) -> ValidationRule:
        """Validação para números inteiros."""
        def validate(value: str) -> bool:
            try:
                num = int(value)
                if min_val is not None and num < min_val:
                    return False
                if max_val is not None and num > max_val:
                    return False
                return True
            except ValueError:
                return False
        
        range_text = ""
        if min_val is not None and max_val is not None:
            range_text = f" (entre {min_val} e {max_val})"
        elif min_val is not None:
            range_text = f" (mínimo {min_val})"
        elif max_val is not None:
            range_text = f" (máximo {max_val})"
        
        return ValidationRule(
            validator=validate,
            error_message=f"Digite um número válido{range_text}"
        )
    
    @staticmethod
    def float_number(min_val: float = None, max_val: float = None) -> ValidationRule:
        """Validação para números decimais."""
        def validate(value: str) -> bool:
            try:
                num = float(value)
                if min_val is not None and num < min_val:
                    return False
                if max_val is not None and num > max_val:
                    return False
                return True
            except ValueError:
                return False
        
        return ValidationRule(
            validator=validate,
            error_message=f"Digite um número decimal válido"
        )
    
    @staticmethod
    def email() -> ValidationRule:
        """Validação para email."""
        def validate(value: str) -> bool:
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, value) is not None
        
        return ValidationRule(
            validator=validate,
            error_message="Digite um email válido (exemplo@dominio.com)"
        )
    
    @staticmethod
    def url() -> ValidationRule:
        """Validação para URL."""
        def validate(value: str) -> bool:
            import re
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            return re.match(pattern, value) is not None
        
        return ValidationRule(
            validator=validate,
            error_message="Digite uma URL válida (http://exemplo.com)"
        )
    
    @staticmethod
    def path_exists() -> ValidationRule:
        """Validação para caminho de arquivo existente."""
        def validate(value: str) -> bool:
            return os.path.exists(value.strip())
        
        return ValidationRule(
            validator=validate,
            error_message="Caminho do arquivo não existe"
        )


class MenuSystem:
    """
    Sistema principal de menus com navegação avançada.
    
    Gerencia pilha de menus, navegação e inputs do usuário.
    """
    
    def __init__(self, theme: MenuTheme = MenuTheme.DEFAULT):
        self.theme = theme
        self.style = self._create_style(theme)
        self.renderer = MenuRenderer(self.style)
        self.menu_stack: List[Menu] = []
        self.current_menu: Optional[Menu] = None
        self.running = False
        self.result_data: Dict[str, Any] = {}
        
    def _create_style(self, theme: MenuTheme) -> MenuStyle:
        """Cria estilo baseado no tema."""
        if theme == MenuTheme.DARK:
            return MenuStyle(
                selection_bg=Back.WHITE,
                selection_fg=Fore.BLACK,
                title_fg=Fore.CYAN,
                text_fg=Fore.WHITE
            )
        elif theme == MenuTheme.LIGHT:
            return MenuStyle(
                selection_bg=Back.BLACK,
                selection_fg=Fore.WHITE,
                title_fg=Fore.BLUE,
                text_fg=Fore.BLACK
            )
        elif theme == MenuTheme.COLORFUL:
            return MenuStyle(
                title_fg=Fore.MAGENTA + Style.BRIGHT,
                subtitle_fg=Fore.CYAN,
                accent_fg=Fore.GREEN,
                success_fg=Fore.GREEN + Style.BRIGHT,
                error_fg=Fore.RED + Style.BRIGHT
            )
        elif theme == MenuTheme.MINIMAL:
            return MenuStyle(
                border_char="─",
                selection_bg=Back.BLACK,
                title_fg=Fore.WHITE,
                icons={'arrow': '>', 'selected': '*', 'unselected': ' '}
            )
        else:
            return MenuStyle()
    
    def run(self, menu: Menu) -> Dict[str, Any]:
        """Executa o sistema de menus."""
        self.current_menu = menu
        self.menu_stack = [menu]
        self.running = True
        
        try:
            if ADVANCED_INPUT:
                return self._run_advanced()
            else:
                return self._run_basic()
        except KeyboardInterrupt:
            logger.info("Menu system interrupted by user")
            return {'interrupted': True}
        finally:
            self.running = False
    
    def _run_advanced(self) -> Dict[str, Any]:
        """Execução com navegação avançada por teclado."""
        while self.running and self.current_menu:
            self.renderer.render_menu(self.current_menu)
            
            try:
                # Wait for key press
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    self._handle_key_press(event.name)
            except Exception as e:
                logger.error(f"Error handling key press: {e}")
                self._show_error("Erro ao processar tecla pressionada")
        
        return self.result_data
    
    def _run_basic(self) -> Dict[str, Any]:
        """Execução básica sem dependências avançadas."""
        while self.running and self.current_menu:
            self.renderer.render_menu(self.current_menu)
            
            try:
                choice = input(f"\n{self.style.accent_fg}Digite sua escolha: {Style.RESET_ALL}").strip()
                self._handle_basic_input(choice)
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error handling input: {e}")
                self._show_error("Erro ao processar entrada")
        
        return self.result_data
    
    def _handle_key_press(self, key_name: str):
        """Processa teclas pressionadas."""
        if not self.current_menu:
            return
        
        visible_items = [item for item in self.current_menu.items if item.visible and item.enabled]
        
        if key_name == 'up':
            self._move_selection(-1)
        elif key_name == 'down':
            self._move_selection(1)
        elif key_name == 'enter':
            self._execute_selected_item()
        elif key_name == 'esc':
            self._go_back()
        elif key_name.isdigit():
            # Direct number selection
            index = int(key_name) - 1
            if 0 <= index < len(visible_items):
                self.current_menu.selected_index = index
                self._execute_selected_item()
    
    def _handle_basic_input(self, choice: str):
        """Processa input básico (números)."""
        if not choice:
            return
        
        if choice == '0':
            self._go_back()
            return
        
        try:
            index = int(choice) - 1
            visible_items = [item for item in self.current_menu.items if item.visible and item.enabled]
            
            if 0 <= index < len(visible_items):
                # Find the actual index in the full items list
                visible_item = visible_items[index]
                actual_index = self.current_menu.items.index(visible_item)
                self.current_menu.selected_index = actual_index
                self._execute_selected_item()
            else:
                self._show_error("Opção inválida")
        except ValueError:
            self._show_error("Digite um número válido")
    
    def _move_selection(self, direction: int):
        """Move seleção para cima ou baixo."""
        if not self.current_menu:
            return
        
        visible_items = [item for item in self.current_menu.items if item.visible and item.enabled]
        if not visible_items:
            return
        
        # Find current position in visible items
        current_item = self.current_menu.items[self.current_menu.selected_index]
        if current_item in visible_items:
            current_pos = visible_items.index(current_item)
        else:
            current_pos = 0
        
        # Calculate new position
        new_pos = (current_pos + direction) % len(visible_items)
        
        # Update selection
        new_item = visible_items[new_pos]
        self.current_menu.selected_index = self.current_menu.items.index(new_item)
        
        # Update scroll offset
        self._update_scroll_offset()
    
    def _update_scroll_offset(self):
        """Atualiza offset de scroll."""
        if not self.current_menu:
            return
        
        max_visible = self.current_menu.max_visible_items
        selected_idx = self.current_menu.selected_index
        
        if selected_idx < self.current_menu.scroll_offset:
            self.current_menu.scroll_offset = selected_idx
        elif selected_idx >= self.current_menu.scroll_offset + max_visible:
            self.current_menu.scroll_offset = selected_idx - max_visible + 1
    
    def _execute_selected_item(self):
        """Executa item selecionado."""
        if not self.current_menu or self.current_menu.selected_index >= len(self.current_menu.items):
            return
        
        item = self.current_menu.items[self.current_menu.selected_index]
        
        if not item.enabled:
            return
        
        try:
            if item.item_type == MenuItemType.ACTION:
                self._execute_action(item)
            elif item.item_type == MenuItemType.SUBMENU:
                self._open_submenu(item)
            elif item.item_type == MenuItemType.INPUT:
                self._handle_input(item)
            elif item.item_type == MenuItemType.TOGGLE:
                self._toggle_item(item)
            elif item.item_type == MenuItemType.BACK:
                self._go_back()
            elif item.item_type == MenuItemType.EXIT:
                self._exit()
        except Exception as e:
            logger.error(f"Error executing menu item {item.key}: {e}")
            self._show_error(f"Erro ao executar ação: {e}")
    
    def _execute_action(self, item: MenuItem):
        """Executa ação do item."""
        if item.action:
            try:
                result = item.action()
                if result is not None:
                    self.result_data[item.key] = result
                self._show_success(f"Ação '{item.title}' executada com sucesso")
            except Exception as e:
                self._show_error(f"Erro ao executar ação: {e}")
    
    def _open_submenu(self, item: MenuItem):
        """Abre submenu."""
        if item.submenu:
            self.menu_stack.append(item.submenu)
            self.current_menu = item.submenu
            self.current_menu.selected_index = 0
            self.current_menu.scroll_offset = 0
    
    def _handle_input(self, item: MenuItem):
        """Processa input do usuário."""
        if not item.input_type:
            return
        
        try:
            if item.input_type == InputType.CHOICE:
                value = self._get_choice_input(item)
            elif item.input_type == InputType.MULTI_CHOICE:
                value = self._get_multi_choice_input(item)
            elif item.input_type == InputType.CONFIRMATION:
                value = self._get_confirmation_input(item)
            elif item.input_type == InputType.PASSWORD:
                value = self._get_password_input(item)
            else:
                value = self._get_text_input(item)
            
            if value is not None:
                self.result_data[item.key] = value
                self._show_success(f"Valor '{value}' salvo para {item.title}")
        except Exception as e:
            self._show_error(f"Erro ao processar input: {e}")
    
    def _get_text_input(self, item: MenuItem) -> Optional[str]:
        """Obtém input de texto."""
        while True:
            prompt = f"\n{self.style.accent_fg}{item.title}: {Style.RESET_ALL}"
            if item.default_value:
                prompt += f"({item.default_value}) "
            
            try:
                value = input(prompt).strip()
                if not value and item.default_value:
                    value = str(item.default_value)
                
                # Validate input
                if self._validate_input(value, item):
                    return value
                
            except EOFError:
                return None
    
    def _get_choice_input(self, item: MenuItem) -> Optional[str]:
        """Obtém input de escolha única."""
        if not item.choices:
            return None
        
        print(f"\n{self.style.accent_fg}{item.title}:{Style.RESET_ALL}")
        for i, choice in enumerate(item.choices, 1):
            print(f"  {i}. {choice}")
        
        while True:
            try:
                choice_input = input(f"\nEscolha (1-{len(item.choices)}): ").strip()
                index = int(choice_input) - 1
                if 0 <= index < len(item.choices):
                    return item.choices[index]
                else:
                    print(f"{self.style.error_fg}Escolha inválida{Style.RESET_ALL}")
            except (ValueError, EOFError):
                return None
    
    def _get_multi_choice_input(self, item: MenuItem) -> Optional[List[str]]:
        """Obtém input de múltipla escolha."""
        if not item.choices:
            return None
        
        print(f"\n{self.style.accent_fg}{item.title} (múltiplas escolhas):{Style.RESET_ALL}")
        for i, choice in enumerate(item.choices, 1):
            print(f"  {i}. {choice}")
        
        try:
            choice_input = input(f"\nEscolhas (ex: 1,3,5): ").strip()
            if not choice_input:
                return []
            
            indices = [int(x.strip()) - 1 for x in choice_input.split(',')]
            return [item.choices[i] for i in indices if 0 <= i < len(item.choices)]
        except (ValueError, EOFError):
            return None
    
    def _get_confirmation_input(self, item: MenuItem) -> Optional[bool]:
        """Obtém confirmação sim/não."""
        while True:
            try:
                response = input(f"\n{self.style.accent_fg}{item.title} (s/n): {Style.RESET_ALL}").strip().lower()
                if response in ['s', 'sim', 'y', 'yes']:
                    return True
                elif response in ['n', 'não', 'nao', 'no']:
                    return False
                else:
                    print(f"{self.style.error_fg}Digite 's' para sim ou 'n' para não{Style.RESET_ALL}")
            except EOFError:
                return None
    
    def _get_password_input(self, item: MenuItem) -> Optional[str]:
        """Obtém input de senha (oculto)."""
        try:
            import getpass
            return getpass.getpass(f"\n{self.style.accent_fg}{item.title}: {Style.RESET_ALL}")
        except:
            # Fallback para input normal se getpass não estiver disponível
            return input(f"\n{self.style.accent_fg}{item.title}: {Style.RESET_ALL}")
    
    def _validate_input(self, value: str, item: MenuItem) -> bool:
        """Valida input do usuário."""
        for rule in item.validation_rules:
            if not rule.validator(value):
                print(f"{self.style.error_fg}Erro: {rule.error_message}{Style.RESET_ALL}")
                return False
        return True
    
    def _toggle_item(self, item: MenuItem):
        """Alterna valor de toggle."""
        item.default_value = not item.default_value
        self.result_data[item.key] = item.default_value
        status = "ativado" if item.default_value else "desativado"
        self._show_success(f"{item.title} {status}")
    
    def _go_back(self):
        """Volta ao menu anterior."""
        if len(self.menu_stack) > 1:
            self.menu_stack.pop()
            self.current_menu = self.menu_stack[-1]
    
    def _exit(self):
        """Sai do sistema de menus."""
        self.running = False
    
    def _show_error(self, message: str):
        """Mostra mensagem de erro."""
        print(f"\n{self.style.error_fg}❌ {message}{Style.RESET_ALL}")
        input(f"{self.style.text_fg}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _show_success(self, message: str):
        """Mostra mensagem de sucesso."""
        print(f"\n{self.style.success_fg}✅ {message}{Style.RESET_ALL}")
        time.sleep(1)  # Brief pause to show success message
    
    def _show_warning(self, message: str):
        """Mostra mensagem de aviso."""
        print(f"\n{self.style.warning_fg}⚠️ {message}{Style.RESET_ALL}")
        time.sleep(1)


# Factory functions for common menu types
def create_main_menu(title: str = "Menu Principal") -> Menu:
    """Cria menu principal padrão."""
    menu = Menu(title)
    menu.add_separator("Opções Principais")
    return menu


def create_settings_menu() -> Menu:
    """Cria menu de configurações padrão."""
    menu = Menu("Configurações", "Ajuste as configurações do sistema")
    
    menu.add_input(
        "log_level", 
        "Nível de Log",
        InputType.CHOICE,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default_value="INFO"
    )
    
    menu.add_input(
        "max_workers",
        "Número máximo de workers",
        InputType.NUMBER,
        validation_rules=[InputValidator.number(1, 20)],
        default_value=3
    )
    
    menu.add_toggle("enable_ai", "Habilitar IA", default_value=True)
    menu.add_toggle("auto_backup", "Backup automático", default_value=True)
    
    menu.add_separator()
    menu.add_back()
    
    return menu


# Export principais
__all__ = [
    'MenuSystem', 'Menu', 'MenuItem', 'MenuItemType', 'InputType',
    'MenuTheme', 'MenuStyle', 'ValidationRule', 'InputValidator',
    'create_main_menu', 'create_settings_menu'
]