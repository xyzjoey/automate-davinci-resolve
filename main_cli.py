from argparse import ArgumentParser

from davinci_resolve_cli.app.app import App
from davinci_resolve_cli.davinci.resolve_app import ResolveApp
from davinci_resolve_cli.utils.log import Log


if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("action", type=str)
    argparser.add_argument("input_data", type=eval)
    args = argparser.parse_args()

    resolve_app = ResolveApp()
    app = App(resolve_app)

    Log.init()

    app.start_action(args.action, args.input_data)
