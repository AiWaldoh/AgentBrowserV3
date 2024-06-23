import time
from colorama import init, Fore, Style
import os


def print_welcome_message():
    init()  # Initialize colorama for color support

    # Clear the console screen
    os.system("cls" if os.name == "nt" else "clear")

    # Define the ASCII art
    ascii_art = r"""
    {cyan}╔════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                ║
    ║        {green}██╗    ██╗███████╗██╗      ██████╗ ██████╗ ███╗   ███╗███████╗{cyan}          ║
    ║        {green}██║    ██║██╔════╝██║     ██╔════╝██╔═══██╗████╗ ████║██╔════╝{cyan}          ║
    ║        {green}██║ █╗ ██║█████╗  ██║     ██║     ██║   ██║██╔████╔██║█████╗{cyan}            ║
    ║        {green}██║███╗██║██╔══╝  ██║     ██║     ██║   ██║██║╚██╔╝██║██╔══╝{cyan}            ║
    ║        {green}╚███╔███╔╝███████╗███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗{cyan}          ║
    ║         {green}╚══╝╚══╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝{cyan}          ║
    ║                                                                                ║
    ║                  {yellow}★ Your Ultimate CLI Browser Experience ★{cyan}                      ║
    ║                                                                                ║
    ║  {magenta}Get ready to embark on a captivating journey through the realms of the web!{cyan}   ║
    ║    {magenta}Prepare to witness the fusion of power, convenience, and innovation.{cyan}        ║
    ║        {magenta}Brace yourself for an unparalleled browsing adventure like{cyan}              ║
    ║                        {magenta}no other, right in your CLI!{cyan}                            ║
    ║                                                                                ║
    ╚════════════════════════════════════════════════════════════════════════════════╝
    """

    # Print the ASCII art with colors
    print(
        ascii_art.format(
            cyan=Fore.CYAN, green=Fore.GREEN, yellow=Fore.YELLOW, magenta=Fore.MAGENTA
        )
    )

    # Print additional information with typewriter effect
    typewriter_text = (
        f"\n  Prepare to unleash the full potential of the web at your fingertips!"
    )
    for char in typewriter_text:
        print(char, end="", flush=True)
        time.sleep(0.05)

    # Wait for a short pause before clearing the screen
    time.sleep(2)
    print("\n")
