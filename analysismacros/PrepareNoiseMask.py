import yaml
import argparse
import ROOT
import array as a
import numpy as np

def main():

    #HS-L B0
    coltochipid0l = {0:16, 1:17, 2:18, 3:19, 4:20, 5:21, 6:22,
                    7:32, 8:33, 9:34, 10:35, 11:36, 12:37, 13:38,
                    14:48, 15:49, 16:50, 17:51, 18:52, 19:53, 20:54,
                    21:64, 22:65, 23:66, 24:67, 25:68, 26:69, 27:70,
                    28:80, 29:81, 30:82, 31:83, 32:84, 33:85, 34:86,
                    35:96, 36:97, 37:98, 38:99, 39:100, 40:101, 41:102,
                    42:112, 43:113, 44:114, 45:115, 46:116, 47:117, 48:118}
    #HS-L A8
    coltochipid8l = {0:30, 1:29, 2:28, 3:27, 4:26, 5:25, 6:24,
                    7:46, 8:45, 9:44, 10:43, 11:42, 12:41, 13:40,
                    14:62, 15:61, 16:60, 17:59, 18:58, 19:57, 20:56,
                    21:78, 22:77, 23:76, 24:75, 25:74, 26:73, 27:72,
                    28:94, 29:93, 30:92, 31:91, 32:90, 33:89, 34:88,
                    35:110, 36:109, 37:108, 38:107, 39:106, 40:105, 41:104,
                    42:126, 43:125, 44:124, 45:123, 46:122, 47:121, 48:120}
    #HS-U B0
    coltochipid0u = {0:144, 1:145, 2:146, 3:147, 4:148, 5:149, 6:150,
                    7:160, 8:161, 9:162, 10:163, 11:164, 12:165, 13:166,
                    14:176, 15:177, 16:178, 17:179, 18:180, 19:181, 20:182,
                    21:192, 22:193, 23:194, 24:195, 25:196, 26:197, 27:198,
                    28:208, 29:209, 30:210, 31:211, 32:212, 33:213, 34:214,
                    35:224, 36:225, 37:226, 38:227, 39:228, 40:229, 41:230,
                    42:240, 43:241, 44:242, 45:243, 46:244, 47:245, 48:246}

    #HS-U A8
    coltochipid8u = {0:158, 1:157, 2:156, 3:155, 4:154, 5:153, 6:152,
                    7:174, 8:173, 9:172, 10:171, 11:170, 12:169, 13:168,
                    14:190, 15:189, 16:188, 17:187, 18:186, 19:185, 20:184,
                    21:206, 22:205, 23:204, 24:203, 25:202, 26:201, 27:200,
                    28:222, 29:221, 30:220, 31:219, 32:218, 33:217, 34:216,
                    35:238, 36:237, 37:236, 38:235, 39:234, 40:233, 41:232,
                    42:254, 43:253, 44:252, 45:251, 46:250, 47:249, 48:248}

    rowselector = {0: coltochipid0l, 1: coltochipid8l, 2: coltochipid0u, 3: coltochipid8u}

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, help="Input file to be analysed")
    args = parser.parse_args()
    print(f"Analysing file: {args.file}")

    #open file
    infl = ROOT.TFile.Open(args.file, "READ")
    ntriggers = GetTriggers(infl)
    print(f"Number of triggers: {ntriggers}")
    #Loop over all THnSparse and prepare yaml file with noisy pixels
    NOISECUT = 1e-6
    for key in infl.GetListOfKeys():
        obj=key.ReadObj()
        if obj.InheritsFrom("THnSparse"):
            if obj.GetEntries()-1 < 0: #skip empty THnSparse
                continue
            ## Loop of pixels which fired
            layer = obj.GetName()[9:10]
            dict = {}
            npix = 0
            for ibin in range(obj.GetNbins()):
                coord = np.array([0,0], dtype=np.int32)
                pixelhits = obj.GetBinContent(ibin, np.asarray(coord))
                fhr = pixelhits/ntriggers #fhr of the pixel
                if fhr < NOISECUT: ##noise cut
                    continue
                npix = npix+1
                chipid = 0
                if int(layer)<3: #ib
                    chipid = int((coord[0]-1)/1024)
                    if chipid not in dict:
                        dict.update({chipid:[[int(coord[0]-1-chipid*1024),int(coord[1]-1),fhr]]})
                    else:
                        dict[chipid].append([int(coord[0]-1-chipid*1024),int(coord[1]-1),fhr])
                else: #ob - to be added
                    rowidx = int(int(coord[1]-1) / 512)
                    colidx = int(int(coord[0]-1) / 1024)
                    chipid = rowselector[rowidx][colidx]
                    if chipid not in dict:
                        dict.update({chipid:[[int(coord[0]-1-colidx*1024),int(coord[1]-1)-rowidx*512,fhr]]})
                    else:
                        dict[chipid].append([int(coord[0]-1-colidx*1024),int(coord[1]-1)-rowidx*512,fhr])
            ##save yaml
            if int(layer)<3:
                continue
            stavenum = obj.GetName()[14:15] if obj.GetName()[15:16] == "_" else obj.GetName()[14:16]
            print(f"L{layer}_{int(stavenum):02d}: {npix} hot pixels above cut")
            with open(f"../yaml/noise_masks/L{layer}_{int(stavenum):02d}.yml", 'w') as f:
                yaml.dump(dict, f)


## Function to get number of triggers
def GetTriggers(infl):
    fhr_chip_ib = 0.
    nhits_chip_ib = 0.
    for key in infl.GetListOfKeys():
        obj=key.ReadObj()
        name = obj.GetName()
        if obj.InheritsFrom("TH2") and ("L0" in name): ##just take L0
            fhr_chip_ib = obj.GetBinContent(1,1)
            if fhr_chip_ib<1e-15:
                print("Please change chip, this bin is empty")
        if obj.InheritsFrom("THnSparse") and ("L0_Stv0" in name): ##just take L0_00
            h2 = obj.Projection(1,0)
            nhits_chip_ib = h2.Integral(1,1024,1,512)
            del h2
            break
    return nhits_chip_ib / (512.*1024.*fhr_chip_ib)

if __name__ == '__main__':
    main()