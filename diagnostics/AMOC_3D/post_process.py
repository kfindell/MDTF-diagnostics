#============================================================
# execute_ncl_calculate - call a nclPlotFile via subprocess call
#============================================================
def execute_ncl_calculate(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call

    Arguments:
    nclPlotFile (string) - full path to ncl plotting file name
    """
    import subprocess
    # check if the nclPlotFile exists -
    # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl -Q {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0]
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

#============================================================
# create html3
#============================================================
def create_html3():
    '''
    ----------------------------------------------------------------------
    Note
        create html of QTS figures, all models into one html
    ----------------------------------------------------------------------
    '''
    import os
    import re

    print("creating html2 ...")
    html=os.environ["HTMDIR"]+"/template2.html"
    html2=os.environ["WKDIR"]+"/AMOC_3D_Structure.html"
    print(os.environ["WKDIR"])
    if os.path.isfile(html):
        fp = file(html)
        lines = fp.readlines()
        head = lines[0:110]
        partA= lines[110:125]
        midd = lines[125:167]
        partB= lines[167:178]
        tail = lines[178:193]
        fp.close()
        fp2= file(html2, 'w')
        head=[i.replace("CanESM2",os.environ["CASENAME"]) for i in head]
        midd=[i.replace("CanESM2",os.environ["CASENAME"]) for i in midd]
        tail=[i.replace("CanESM2",os.environ["CASENAME"]) for i in tail]
        models=os.environ["MODELS"].replace(' ','')
        cnt = 110
        for model in models.split(','):
            print model
            for i in partA:
                i=i.replace("CanESM2",model)
                head.insert(cnt, i)
                cnt = cnt +1
        cnt = 42
        for model in models.split(','):
            for i in partB:
                i=i.replace("CanESM2",model)
                midd.insert(cnt, i)
                cnt = cnt +1
        s = ''.join(head+midd+tail)
        fp2.write(s)
        fp2.close()
        print(html2)
#============================================================
# create html2
#============================================================
def create_html2():
    '''
    ----------------------------------------------------------------------
    Note
        create html of QTS figures, all models into one html
    ----------------------------------------------------------------------
    '''
    import os
    import re

    print("creating html2 ...")
    html=os.environ["HTMDIR"]+"/template2.html"
    html2=os.environ["WKDIR"]+"/AMOC_3D_Structure.html"
    print(os.environ["WKDIR"])
    if os.path.isfile(html):
        fp = file(html)
        lines = fp.readlines()
        head = lines[0:45]
        partA= lines[45:61]
        tail = lines[61:85]
        partB= lines[85:97]
        fp.close()
        fp2= file(html2, 'w')
        head=[i.replace("CanESM2",os.environ["CASENAME"]) for i in head]
        tail=[i.replace("CanESM2",os.environ["CASENAME"]) for i in tail]
        models=os.environ["MODELS"].replace(' ','')
        cnt = 45
    #      for model in re.split('[ ,]', os.environ["MODELS"]):
        for model in models.split(','):
            print model
            for i in partA:
                i=i.replace("CanESM2",model)
                head.insert(cnt, i)
                cnt = cnt +1
    #      print model
        cnt = 24
    #      for model in re.split('[ ,]', os.environ["MODELS"]):
        for model in models.split(','):
    #         print model
            for i in partB:
                i=i.replace("CanESM2",model)
                tail.insert(cnt, i)
                cnt = cnt +1
        s = ''.join(head+tail)
        fp2.write(s)
        fp2.close()
        print(html2)
#============================================================
# create html
#============================================================
def create_html(model):
    '''
    ----------------------------------------------------------------------
    Note
        create html of QTS figures
    ----------------------------------------------------------------------
    '''
    import os

    print(model+": creating html ...")
    html=os.environ["HTMDIR"]+"template.html"
    html2=os.environ["QTSDIR"]+"AMOC_3D_Structure.html"
    if os.path.isfile(html):
        fp = file(html)
        lines = fp.readlines()
        head = lines[0:45]
        partA= lines[45:61]
        tail = lines[61:85]
        partB= lines[85:97]
        fp.close()
        fp2= file(html2, 'w')
        cnt = 45
    #      print model
        for i in partA:
            i=i.replace("CanESM2",model)
            head.insert(cnt, i)
            cnt = cnt +1
        cnt = 24
    #      print model
        for i in partB:
            i=i.replace("CanESM2",model)
            tail.insert(cnt, i)
            cnt = cnt +1
        s = ''.join(head+tail)
        fp2.write(s)
        fp2.close()
#============================================================
# convert pdf to png
#============================================================
def convert_pdf2png():
    '''
    ----------------------------------------------------------------------
    Note
        convert pdf figures to png format
    ----------------------------------------------------------------------
    '''
    import os

    print("Converting *.pdf to *.png ...")
    if os.environ["CLEAN"] == "1":
        os.system("rm -rf "+os.environ["OUTDIR"])
        os.system("rm -rf "+os.environ["FIGDIR"])

    files = os.listdir(os.environ["FIGDIR"])
    a = 0
    while a < len(files):
        file1 = os.environ["FIGDIR"]+files[a]
        if file1[-3:] == ".png":
            a = a + 1
            continue
        file2 = os.environ["PNGDIR"]+files[a]
        os.system("pdfcrop --margins '5 5 5 5' "+file1+" "+file2+"; convert -density 400 "+file2+" -quality 100 "+file2[:-4]+".png")
        a = a+1
#    os.system("rm -f "+os.environ["FIGDIR"]+"*.*")
    os.system("\mv "+os.environ["PNGDIR"]+"*.pdf "+os.environ["FIGDIR"])
#    os.system("\mv "+os.environ["PNGDIR"]+"*.png "+os.environ["FIGDIR"])

#============================================================
# convert pdf to png for obs/reference
#============================================================
def convert_pdf2png_obs():
    '''
    ----------------------------------------------------------------------
    Note
        convert pdf figures to png format
    ----------------------------------------------------------------------
    '''
    import os
    print("Converting pdf to png ...")
    files = os.listdir(os.environ["FIGREF"])
    print(files)
    a = 0
    while a < len(files):
        file1 = os.environ["FIGREF"]+files[a]
        if file1[-3:] == ".png":
            a = a + 1
            continue
        file2 = os.environ["PNGREF"]+files[a]
        os.system("pdfcrop --margins '5 5 5 5' "+file1+" "+file2+"; convert -density 400 "+file2+" -quality 100 "+file2[:-4]+".png")
        a = a+1
#    os.system("rm -f "+os.environ["FIGREF"]+"*.*")
    os.system("\mv "+os.environ["PNGREF"]+"*.pdf "+os.environ["FIGREF"])
#    os.system("\mv "+os.environ["PNGREF"]+"*.png "+os.environ["FIGREF"])

#============================================================
# move monthly and yearly files to mon_yr/
#============================================================
def mv_mon_yr(model):
    '''
    ----------------------------------------------------------------------
    Note
        mv *.mon.nc *.yr.nc to mon_yr/
    ----------------------------------------------------------------------
    '''
    import os
    import glob
    print(model+": mv *.mon.nc *.yr.nc to mon_yr/ ...")
    if len(glob.glob(os.environ["TMPDIR"]+model+".*.mon.nc"))>0:
        print("mv monthly files to "+os.environ["TMPDIR"]+"mon_yr/")
        os.system("mv "+os.environ["OUTDIR"]+model+".*.mon.nc "+os.environ["TMPDIR"])

    if len(glob.glob(os.environ["OUTDIR"]+model+".*.yr.nc"))>0:
        print("mv yearly files to "+os.environ["OUTDIR"]+"mon_yr/")
        os.system("\mv "+os.environ["OUTDIR"]+model+".*.yr.nc "+os.environ["TMPDIR"])    
