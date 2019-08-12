import os
import sys
import glob
import shutil
from distutils.spawn import find_executable #determine if a program is on $PATH
import util
from util import setenv # TODO: fix

class Diagnostic(object):
    # analogue of TestCase in xUnit

    def __init__(self, pod_name, verbose=0):
        self.name = pod_name
        self.dir = os.path.join(os.environ['DIAG_HOME'], 'diagnostics', self.name)
        # assert(os.path.isdir(pod_dir))
        file_contents = util.read_yaml(os.path.join(self.dir, 'settings.yml'))

        config = self._parse_pod_settings(file_contents['settings'], verbose)
        self.__dict__.update(config)
        config = self._parse_pod_varlist(file_contents['varlist'], verbose)
        self.varlist = config

    def _parse_pod_settings(self, settings, verbose=0):
        d = {}
        d['pod_name'] = self.name # redundant
        # define empty defaults to avoid having to test existence of attrs
        for str_attr in ['program', 'driver', 'long_name', 'description', 
            'conda_env']:
            d[str_attr] = ''
        for list_attr in ['varlist', 'found_files', 'missing_files']:
            d[list_attr] = []
        for dict_attr in ['pod_env_vars']:
            d[dict_attr] = {}
        for obj_attr in ['process_obj', 'logfile_obj']:
            d[obj_attr] = None

        # overwrite with contents of settings.yaml file
        d.update(settings)
        if d['conda_env'] == '':
            d['conda_env'] = '_MDTF-diagnostics'
        elif not d['conda_env'].startswith('_MDTF-diagnostics'):
            d['conda_env'] = '-'.join(['_MDTF-diagnostics', d['conda_env']])
        if (verbose > 0): 
            print self.name + " settings: "
            print d
        return d

    def _parse_pod_varlist(self, varlist, verbose=0):
        default_file_required = False 
        for idx, var in enumerate(varlist):
            varlist[idx]['name_in_model'] = \
                util.translate_varname(var['var_name'], verbose=verbose)

            assert(var['freq'] in ['1hr', '3hr', '6hr', 'day', 'mon']), \
                "WARNING: didn't find "+var['freq']+" in frequency options "+\
                    " (set in "+__file__+": parse_pod_varlist)"
            if 'requirement' in var:
                varlist[idx]['required'] = (var['requirement'].lower() == 'required')
            else:
                varlist[idx]['required'] = default_file_required
            if ('alternates' in var) and (type(var['alternates']) is not list):
                varlist[idx]['alternates'] = [var['alternates']]
        if (verbose > 0): 
            print self.name + " varlist: "
            print varlist
        return varlist

    # -------------------------------------

    def setUp(self, verbose=0):
        self._set_pod_env_vars(verbose)
        self._setup_pod_directories()

        self._check_pod_driver(verbose)
        var_files = self._check_for_varlist_files(verbose)
        self.found_files = var_files['found_files']
        self.missing_files = var_files['missing_files']

    def _set_pod_env_vars(self, verbose=0):
        pod_envvars = {}
        # location of POD's code
        setenv("POD_HOME", 
            os.path.join(os.environ["DIAG_HOME"], 'diagnostics', self.name),
            pod_envvars, overwrite=False, verbose=verbose)
        # POD's observational data
        setenv("OBS_DATA",
            os.path.join(os.environ["OBS_ROOT_DIR"], self.name),
            pod_envvars, overwrite=False, verbose=verbose)
        # POD's subdir within working directory
        setenv("WK_DIR", 
            os.path.join(os.environ['variab_dir'], self.name),
            pod_envvars,overwrite=False,verbose=verbose)
        util.check_required_dirs(
            already_exist =["POD_HOME", 'OBS_DATA'], create_if_nec = ["WK_DIR"], 
            verbose=verbose)

        # optional POD-specific env vars defined in settings.yml
        for key, val in self.pod_env_vars.items():
            setenv(key, val, pod_envvars, overwrite=False, verbose=verbose)
        
        return pod_envvars

    def _setup_pod_directories(self):
        pod_wk_dir = os.path.join(os.environ['variab_dir'], self.name)
        dirs = ['', 'model', 'model/PS', 'model/netCDF', 'obs', 'obs/PS','obs/netCDF']
        for d in dirs:
            if not os.path.exists(os.path.join(pod_wk_dir, d)):
                os.makedirs(os.path.join(pod_wk_dir, d))

    def _check_pod_driver(self, verbose=0):
        func_name = "check_pod_driver "
        if (verbose > 1):  print func_name," received POD settings: ", self.__dict__
        programs = util.get_available_programs()

        if self.driver == '':  
            print "WARNING: no valid driver entry found for ", self.name
            #try to find one anyway
            try_filenames = [self.name+".", "driver."]      
            file_combos = [ file_root + ext for file_root in try_filenames for ext in programs.keys()]
            if verbose > 1: 
                print "Checking for possible driver names in ",self.dir," ",file_combos
            for try_file in file_combos:
                try_path = os.path.join(self.dir, try_file)
                if verbose > 1: print " looking for driver file "+try_path
                if os.path.exists(try_path):
                    self.driver = try_path
                    if (verbose > 0): print "Found driver script for "+self.name+" : "+ self.driver
                    break    #go with the first one found
                else:
                    if (verbose > 1 ): print "\t "+try_path+" not found..."
        errstr_nodriver = "No driver script found for package "+self.name +"\n\t"\
            +"Looked in "+self.dir+" for pod_name.* or driver.* \n\t"\
            +"To specify otherwise, add a line to "+self.name+"/settings file containing:  driver driver_script_name \n\t" \
            +"\n\t"+func_name
        assert (self.driver != ''), errstr_nodriver

        if not os.path.isabs(self.driver): # expand relative path
            self.driver = os.path.join(self.dir, self.driver)
        errstr = "ERROR: "+func_name+" can't find "+ self.driver+" to run "+self.name
        assert(os.path.exists(self.driver)), errstr 

        if self.program == '':
            # Find ending of filename to determine the program that should be used
            driver_ext  = self.driver.split('.')[-1]
            # Possible error: Driver file type unrecognized
            errstr_badext = func_name+" does not know how to call a ."+driver_ext+" file \n\t"\
                +"Available programs: "+str(programs.keys())
            assert (driver_ext in programs), errstr_badext
            self.program = programs[driver_ext]
            if ( verbose > 1): print func_name +": Found program "+programs[driver_ext]
        errstr = "ERROR: "+func_name+" can't find "+ self.program+" to run "+self.name
        assert(find_executable(self.program) is not None), errstr     

    def _check_for_varlist_files(self, varlist, verbose=0):
        func_name = "\t \t check_for_varlist_files :"
        if ( verbose > 2 ): print func_name+" check_for_varlist_files called with ",varlist
        found_list = []
        missing_list = []
        for item in varlist:
            if (verbose > 2 ): print func_name +" "+item
            filepath = util.makefilepath(item['name_in_model'],item['freq'],os.environ['CASENAME'],os.environ['DATADIR'])

            if (os.path.isfile(filepath)):
                print "found ",filepath
                found_list.append(filepath)
                continue
            if (not item['required']):
                print "WARNING: optional file not found ",filepath
                continue
            if not (('alternates' in item) and (len(item['alternates'])>0)):
                print "ERROR: missing required file ",filepath,". No alternatives found"
                missing_list.append(filepath)
            else:
                alt_list = item['alternates']
                print "WARNING: required file not found ",filepath,"\n \t Looking for alternatives: ",alt_list
                for alt_item in alt_list: # maybe some way to do this w/o loop since check_ takes a list
                    if (verbose > 1): print "\t \t examining alternative ",alt_item
                    new_var = item.copy()  # modifyable dict with all settings from original
                    new_var['name_in_model'] = util.translate_varname(alt_item,verbose=verbose)  # alternative variable name 
                    del new_var['alternates']    # remove alternatives (could use this to implement multiple options)
                    if ( verbose > 2): print "created new_var for input to check_for_varlist_files",new_var
                    new_files = self._check_for_varlist_files([new_var],verbose=verbose)
                    found_list.extend(new_files['found_files'])
                    missing_list.extend(new_files['missing_files'])

        if (verbose > 2): print "check_for_varlist_files returning ",missing_list
        # remove empty list entries
        files = {}
        files['found_files'] = [x for x in found_list if x]
        files['missing_files'] = [x for x in missing_list if x]
        return files

    # -------------------------------------

    def run(self):
        # TODO: what to do with this? running handled by Environment
        pass

    # -------------------------------------

    def tearDown(self, verbose=0):
        # shouldn't need to re-set env vars, but used by 
        # convective_transition_diag to set filename info 
        self._set_pod_env_vars(verbose=verbose)

        self._make_pod_html()
        self._convert_pod_figures()
        self._cleanup_pod_files()

        if verbose > 0: 
            print("---  MDTF.py Finished POD "+self.name+"\n")
            # elapsed = timeit.default_timer() - start_time
            # print(pod+" Elapsed time ",elapsed)

    def _make_pod_html(self):
        # do templating on POD's html file
        pod_code_dir = os.path.join(os.environ['DIAG_HOME'], 'diagnostics', self.name)
        pod_wk_dir = os.path.join(os.environ['variab_dir'], self.name)
        html_file = os.path.join(pod_wk_dir, self.name+'.html')
        temp_file = os.path.join(pod_wk_dir, 'tmp.html')

        if os.path.exists(html_file):
            os.remove(html_file)
        shutil.copy2(os.path.join(pod_code_dir, self.name+'.html'), pod_wk_dir)
        os.system("cat "+ html_file \
            + " | sed -e s/casename/" + os.environ["CASENAME"] + "/g > " \
            + temp_file)
        # following two substitutions are specific to convective_transition_diag
        # need to find a more elegant way to handle this
        if self.name == 'convective_transition_diag':
            temp_file2 = os.path.join(pod_wk_dir, 'tmp2.html')
            if ("BULK_TROPOSPHERIC_TEMPERATURE_MEASURE" in os.environ) \
                and os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"] == "2":
                os.system("cat " + temp_file \
                    + " | sed -e s/_tave\./_qsat_int\./g > " + temp_file2)
                shutil.move(temp_file2, temp_file)
            if ("RES" in os.environ) and os.environ["RES"] != "1.00":
                os.system("cat " + temp_file \
                    + " | sed -e s/_res\=1\.00_/_res\=" + os.environ["RES"] + "_/g > " \
                    + temp_file2)
                shutil.move(temp_file2, temp_file)
        shutil.copy2(temp_file, html_file) 
        os.remove(temp_file)

        # add link and description to main html page
        html_file = os.path.join(os.environ["variab_dir"], 'index.html')
        a = os.system("cat " + html_file + " | grep " + self.name)
        if a != 0:
            os.system("echo '<H3><font color=navy>" + self.description \
                + " <A HREF=\""+ self.name+"/"+self.name+".html\">plots</A></H3>' >> " \
                + html_file)

    def _convert_pod_figures(self):
        # Convert PS to png
        pod_wk_dir = os.path.join(os.environ['variab_dir'], self.name)
        dirs = ['figures', 'model/PS', 'obs/PS']
        for d in dirs:
            full_path = os.path.join(pod_wk_dir, d)
            files = glob.glob(full_path+"/*.ps")
            files.extend(glob.glob(full_path+"/*.eps"))
            for f in files:
                (dd, ff) = os.path.split(os.path.splitext(f)[0])
                ff = os.path.join(os.path.dirname(dd), ff) # parent directory/filename
                command_str = 'convert '+ os.environ['convert_flags'] + ' ' \
                    + f + ' ' + ff + '.' + os.environ['convert_output_fmt']
                os.system(command_str)   

    def _cleanup_pod_files(self):
        pod_name = self.name
        pod_code_dir = os.path.join(os.environ['DIAG_HOME'], 'diagnostics', pod_name)
        pod_data_dir = os.path.join(os.environ['OBS_ROOT_DIR'], pod_name)
        pod_wk_dir = os.path.join(os.environ['variab_dir'], pod_name)

        # copy PDF documentation (if any) to output
        files = glob.glob(pod_code_dir+"/*.pdf")
        for file in files:
            shutil.copy2(file, pod_wk_dir)

        # copy premade figures (if any) to output 
        files = glob.glob(pod_data_dir+"/*.gif")
        files.extend(glob.glob(pod_data_dir+"/*.png"))
        files.extend(glob.glob(pod_data_dir+"/*.jpg"))
        files.extend(glob.glob(pod_data_dir+"/*.jpeg"))
        for file in files:
            shutil.copy2(file, pod_wk_dir+"/obs")

        # remove .eps files if requested
        if os.environ["save_ps"] == "0":
            dirs = ['model/PS', 'obs/PS']
            for d in dirs:
                if os.path.exists(os.path.join(pod_wk_dir, d)):
                    shutil.rmtree(os.path.join(pod_wk_dir, d))

        # delete netCDF files if requested
        if os.environ["save_nc"] == "0":    
            dirs = ['model/netCDF', 'obs/netCDF']
            for d in dirs:
                if os.path.exists(os.path.join(pod_wk_dir, d)):
                    shutil.rmtree(os.path.join(pod_wk_dir, d))