from argparse import ArgumentParser

from automate_davinci_resolve.app.app import App
from automate_davinci_resolve.davinci.resolve_app import ResolveApp
from automate_davinci_resolve.utils.log import Log

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("action", type=str)
    argparser.add_argument("input_data", type=eval)
    args = argparser.parse_args()

    resolve_app = ResolveApp()
    app = App(resolve_app)

    Log.init()

    app.start_action(args.action, args.input_data)
