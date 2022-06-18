from tkinter import filedialog
import codecs

def get_txtpath():
    txtpath = filedialog.askopenfilename(filetypes = [('text files','*.txt'),('all files','*.*')])
    return txtpath

def foreachline_in_txtfile(txtpath, callback):
    if not txtpath:
        return

    txtfile = codecs.open(txtpath, 'r', 'utf-8')

    line = txtfile.readline()
    while line:
        callback(line)
        line = txtfile.readline()

    txtfile.close()

def get_emptyduration():
    return 30

def get_duration(s):
    return len(s) * 5 + 30

def generate_text_frame_info():
    txtpath = get_txtpath()

    if not txtpath:
        return None

    info_format = ('[%d] = { %d , Flags = { Linear = true, LockedY = true }, Value = Text {\n' +
                    ' '*8 + 'Value = "%s"\n' +
                    ' '*4 + '} },\n')
    info_str = ''
    lineindex = -1
    starttime = 0
    is_prev_empty = False

    def foreach_callback(line):
        nonlocal info_str, lineindex, starttime, is_prev_empty

        endtime = starttime
        line = line.strip()

        if line.startswith('#'):
            return
        elif not line and not is_prev_empty:
            endtime = starttime + get_emptyduration()
            is_prev_empty = True
        else:
            endtime = starttime + get_duration(line)
            lineindex += 1
            is_prev_empty = False

        info_str += info_format % (starttime, lineindex, line)
        starttime = endtime

    foreachline_in_txtfile(txtpath, foreach_callback)
    info_str += (info_format % (starttime, lineindex, ' '))[:-2]

    return info_str

def main():
    info_str = generate_text_frame_info()
    print(info_str)

if __name__ == "__main__":
    main()
