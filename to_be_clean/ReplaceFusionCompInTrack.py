from tkinter import filedialog

# COMPPATH_DEFAULT = 'D:/XYZ/YOUTUBE/DavinciResolve/subtitle.comp'
TARGETTRACK_DEFAULT = {
    'type': 'video',
    'index': 1,
}

pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject()

def getDataToKeep(comp):
    data = {
        'text': comp.FindToolByID('TextPlus').GetInput('StyledText'),
    }
    return data

def setData(comp, data):
    comp.FindToolByID('TextPlus').SetInput('StyledText', data['text'])

def replaceFusionCompInTrack():
    newCompPath = filedialog.askopenfilename(filetypes = [('comp files','*.comp'),('all files','*.*')])
    targetTrack = TARGETTRACK_DEFAULT
    targetTrack['index'] = int(input('Enter video track index (start from 1): '))

    tl = proj.GetCurrentTimeline()

    print('new fusion comp path:', newCompPath)
    print('target track:', targetTrack['type'], targetTrack['index'])

    for i, item in enumerate(tl.GetItemListInTrack(targetTrack['type'], targetTrack['index'])):
        print('updating {}-th clip... '.format(i), end='')
        dataToKeep = getDataToKeep(item.GetFusionCompByIndex(1))
        print(item.ImportFusionComp(newCompPath))
        setData(item.GetFusionCompByIndex(1), dataToKeep)

    print('done')
    print('*** please delete render cache for updated clips')

replaceFusionCompInTrack()