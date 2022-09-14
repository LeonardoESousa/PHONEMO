#!/usr/bin/env python3
import sys
import nemo.tools

def main():
    print("#     # ####### #     # #######")
    print("##    # #       ##   ## #     #")
    print("# #   # #       # # # # #     #")
    print("#  #  # #####   #  #  # #     #")
    print("#   # # #       #     # #     #")
    print("#    ## #       #     # #     #")
    print("#     # ####### #     # #######")
    print("----------Photophysics---------\n")
    print("Choose your option:\n")
    print("ENSEMBLE SETUP:")
    print("\t1 - Generate the inputs for the nuclear ensemble calculation")
    print("\t2 - Run the ensemble calculations")
    print("\t3 - Check the progress of the calculations")
    print("\t4 - Abort my calculations")
    print('ABSORPTION:')
    print("\t5 - Generate the absorption spectrum")
    print("EXCITED STATE PROPERTIES (FLUORESCENCE, PHOSPHORESCENCE, ISC):")
    print("\t6 - Estimate rates and compute emission spectrum")
    print('EXCITON ANALYSIS:')
    print("\t7 - Estimate Förster radius, fluorescence lifetime and exciton diffusion lengths")
    print('OTHER FEATURES:')
    print("\t8 - Retrieve last geometry from log file") 
    op = input()
    if op == '1':
        freqlog = nemo.tools.fetch_file("frequency",['.out', '.log'])
        with open(freqlog, 'r') as f:
            for line in f:
                if 'Entering Gaussian System' in line:
                    gauss = True
                else:
                    gauss = False
                break
        if gauss:             
            print('You are using a Gaussian log file.')
            template = nemo.tools.fetch_file("QChem template",['.out', '.in'])
            import lx.tools
            _, _, _, _, _, spec = lx.tools.busca_input(freqlog)
            rem, cm, _ = nemo.tools.busca_input(template)
        else:    
            rem, cm, spec = nemo.tools.busca_input(freqlog)        
        print('\nThe suggested configurations for you are:\n')
        print(rem)
        change = input('Are you satisfied with these parameters? y or n?\n')
        if change.lower() == 'n':     
            rem2 = ''
            for elem in rem.split('\n'):
                if len(elem.split()) > 1:
                    if '$' not in elem:
                        base = nemo.tools.default(elem, f'{elem.split()[0]} is set to: {elem.split()[-1]}. If ok, Enter. Otherwise, type the correct value. Type del to delete line.\n')
                        if base.lower() == 'del':
                            base = ''
                    else:    
                        base = elem
                    rem2 += base+'\n'
            rem = rem2
        rem   += "\n$pcm\ntheory                  IEFPCM\nChargeSeparation        Marcus\nStateSpecific           Perturb\n$end\n"
        static = input("Solvent's static dielectric constant?\n")
        refrac = input("Solvent's refractive index?\n")
        try:
            static = float(static)
            refrac = float(refrac)
        except:
            nemo.tools.fatal_error('Dielectric constant and refractive index must be numbers!')    
        rem += f"\n$solvent\nDielectric              {static}\nOpticalDielectric       {refrac**2}\n$end\n\n"            
        num_ex = input("How many excited states?\n")
        go = False
        while not go:
            try:
                num_ex = int(num_ex)
                go = True
            except:
                print("This must be a number! Try again!\n")
        abs_only = input("Prepare input for absorption or fluorescence spectrum only? (y or n)\n")
        if abs_only.lower() == 'y':
            print('Ok, calculations will only be suitable for absorption or fluorescence spectrum simulations!\n')
            header = f"$comment\n{spec}\n$end\n\n$rem\ncis_n_roots             {num_ex}\ncis_singlets            true\ncis_triplets            true\ncalc_soc                false\nSTS_MOM                 true\nCIS_RELAXED_DENSITY     TRUE\nsolvent_method          PCM"
        else:
            print('Ok, calculations will be suitable for all spectra and ISC rate estimates!\n')
            header = f"$comment\n{spec}\n$end\n\n$rem\ncis_n_roots             {num_ex}\ncis_singlets            true\ncis_triplets            true\ncalc_soc                true\nSTS_MOM                 true\nCIS_RELAXED_DENSITY     TRUE\nsolvent_method          PCM"
        header  =  rem.replace('$rem',header)
        header += f'$molecule\n{cm}\n'
        num_geoms = int(input("How many geometries to be sampled?\n"))
        T = float(input("Temperature in Kelvin?\n"))
        if T <= 0:
            nemo.tools.fatal_error("Have you heard about absolute zero? Goodbye!")
        if gauss:
            import lx.tools
            lx.tools.make_ensemble(freqlog, num_geoms, T, header,'$end\n')
            G, atomos = lx.tools.pega_geom(freqlog)
        else:    
            nemo.tools.make_ensemble(freqlog, num_geoms, T, header,'$end\n')  
            G, atomos = nemo.tools.pega_geom(freqlog)  
        nemo.tools.write_input(atomos,G,rem.replace(f'$rem',"$comment\n{spec}\n$end\n\n$rem\ncis_n_roots             {num_ex}\ncis_singlets            true\ncis_triplets            true\ncalc_soc                false\nSTS_MOM                 false\nCIS_RELAXED_DENSITY     TRUE\n$molecule\n{cm}\n"),'$end\n',"Opt_Lambda.com")    
    elif op == '2':
        nemo.tools.batch() 
    elif op == '3':
        nemo.tools.andamento()
    elif op == '4':
        nemo.tools.abort_batch()
    elif op == '5':
        epsilon, nr = nemo.tools.get_nr() 
        print('The spectrum will be run with the following parameters:\n')
        print(f'Solvent dielectric constant: {epsilon:.3f}')
        print(f'Solvent refractive index: {nr:.3f}\n')
        change = input('Are you satisfied with these parameters? y or n?\n')
        if change.lower() == 'n':
            epsilon = nemo.tools.default(epsilon,f'Solvent dielectric constant is {epsilon:.3f}. If ok, Enter. Otherwise, type value.\n')
            nr      = nemo.tools.default(nr,f'Refractive index is {nr:.3f}. If ok, Enter. Otherwise, type value.\n')
            try:
                epsilon = float(epsilon)
                nr      = float(nr)
            except:
                nemo.tools.fatal_error('Dielectric constant and refractive index must be numbers. Bye!')          
        estados = nemo.tools.ask_states("Absorption from which state (S0, S1, T1 ..)\n")
        nemo.tools.spectra(estados, [epsilon,nr])    
    elif op == '6':
        epsilon, nr = nemo.tools.get_nr()
        print('The rates will be calculated with the following parameters:\n')
        print(f'Solvent dielectric constant: {epsilon:.3f}')
        print(f'Solvent refractive index: {nr:.3f}\n')
        change = input('Are you satisfied with these parameters? y or n?\n')
        if change.lower() == 'n':
            epsilon = nemo.tools.default(epsilon,f'Solvent dielectric constant is {epsilon:.3f}. If ok, Enter. Otherwise, type value.\n')
            nr      = nemo.tools.default(nr,f'Refractive index is {nr:.3f}. If ok, Enter. Otherwise, type value.\n')
            try:
                epsilon = float(epsilon)
                nr      = float(nr)
            except:
                nemo.tools.fatal_error('Dielectric constant and refractive index must be numbers. Bye!')
        state = input('What is the initial state (S1, T1, S2 ...)? Accepts comma separated values Ex: T1,T2\n')
        from nemo.analysis import rates, export_results
        states = state.split(',')
        for state in states:
            res, emi = rates(state,[epsilon,nr])
            export_results(res,emi,[epsilon,nr])
    elif op == '7':
        from lx.tools import ld
        ld()
    elif op == '8':
        freqlog = nemo.tools.fetch_file("log",['.log','.out'])
        rem, cm, spec = nemo.tools.busca_input(freqlog)
        G, atomos = nemo.tools.pega_geom(freqlog)
        nemo.tools.write_input(atomos,G,f'{rem}\n$molecule\n{cm}\n','$end','geom.lx')
        print('Geometry saved in the geom.lx file.')    
    else:
        nemo.tools.fatal_error("It must be one of the options... Goodbye!")


    
if __name__ == "__main__":
    sys.exit(main())        

