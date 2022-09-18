class MediaPoolContext:
    def __init__(self, media_pool):
        self.media_pool = media_pool

    def _iter_items(self, folders):
        current_folder = folders[-1]

        for media_pool_item in current_folder.GetClipList():
            yield media_pool_item, folders

        for subfolder in current_folder.GetSubFolderList():
            yield from self._iter_items(folders + [subfolder])

    def iter_items(self):
        yield from self._iter_items([self.media_pool.GetRootFolder()])

    def find_item(self, condition):
        for item, _ in self.iter_items():
            if condition(item):
                return item

        return None
