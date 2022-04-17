"""
Overhaul of the AOV system for lighting in Houdini
v001 - 03.25.2022 (RajSandhu)
    - Initial code creation
    - Added UI
"""

import hou
from PySide2 import QtCore, QtGui, QtWidgets

# Global Variables
rops_list = []
look_publish = []
look_materials = []
all_materials = []
color_to_aov_nodes = []


def set_rops():
    global rops_list
    selction = hou.selectedNodes()
    for node in selction:
        if 'Redshift_ROP' in str(node.type()):
            rops_list.append(node)
        else:
            continue


def get_rops():
    global rops_list
    rops = rops_list
    return rops


def set_look_list():
    global look_publish
    look_publish = hou.vopNodeTypeCategory().nodeType('studio_rs_mat_publish::1.0').instances()


def get_look_list():
    global look_publish
    looks = look_publish
    return looks


def set_look_materials():
    global look_materials
    looks = get_look_list()
    for look in looks:
        for material in look.children():
            look_materials.append(material)


def get_all_look_materials():
    global look_materials
    materials = look_materials
    return materials


def set_all_materials():
    global all_materials
    all_materials = hou.vopNodeTypeCategory().nodeType('redshift_vopnet').instances()


def get_all_materials():
    global all_materials
    materials = all_materials
    return materials


def get_aov_count(rop):
    count = rop.parm('RS_aov').eval()
    return count


def get_aov_list(rop):
    aov_list = []
    for i in range(get_aov_count(rop)):
        aov_list.append(rop.parm('RS_aovSuffix_{i}'.format(i=i + 1)).eval())
    return aov_list


def aov_check(aov, aov_list):
    if aov in aov_list:
        check = True
    else:
        check = False
    return check


def add_aov(rop, aov_type, aov_name):
    index = get_aov_count(rop) + 1
    aov_list = get_aov_list(rop)

    if not aov_check(aov_name, aov_list):
        rop.parm('RS_aov').set(index)
        rop.parm('RS_aovID_{i}'.format(i=index)).set(aov_type)
        rop.parm('RS_aovSuffix_{i}'.format(i=index)).set(aov_name)
        print('AOV {name} Created'.format(name=aov_name))
    else:
        print("{name} Exists".format(name=aov_name))

    return index


def add_crypto(rop, aov_name, index):
    aov_list = get_aov_list(rop)
    filepath = '`$HOUDINI_PROJECT`/images/`$HIPNAME`/`$OS`_`$AOV`/`$OS`_`$AOV`.$F4.exr'

    if aov_check(aov_name, aov_list):
        rop.parm('RS_aovSuffix_{i}'.format(i=index)).set(aov_name)
        rop.parm('RS_aovCustomPrefix_{i}'.format(i=index)).set(filepath)
        if aov_name == 'U_CRYMAT_matte':
            rop.parm('RS_aovCryptomatteType_{i}'.format(i=index)).set(1)
        if aov_name == 'U_CRYOBJ_matte':
            rop.parm('RS_aovCryptomatteType_{i}'.format(i=index)).set(0)

        print('AOV {name} Created'.format(name=aov_name))
    else:
        print("{name} Exists".format(name=aov_name))


def get_changed_parms(materials):
    parms_changed = []
    refl = False
    refr = False
    ss = False
    emission = False
    vol = False
    for material in materials:
        for node in material.children():
            par = node.parms()
            for p in par:
                if not p.isAtDefault():
                    if 'refl_' in str(p) and refl is False:
                        refl = True
                        parms_changed.append(p)
                    elif 'refr_' in str(p) and refr is False:
                        refr = True
                        parms_changed.append(p)
                    elif 'ss_' in str(p) or 'ms_' in str(p) and ss is False:
                        ss = True
                        parms_changed.append(p)
                    elif 'emission_' in str(p) and emission is False:
                        emission = True
                        parms_changed.append(p)
                    elif 'absorption_' in str(p) and vol is False:
                        vol = True
                        parms_changed.append(p)
                    else:
                        continue

    return parms_changed


def set_color_to_aov():
    global color_to_aov_nodes
    look_mats = get_all_look_materials()
    for mat in look_mats:
        for node in mat.children():
            if 'StoreColorToAOV' in str(node):
                color_to_aov_nodes.append(node)


def get_color_to_aov():
    global color_to_aov_nodes
    colortoaov = color_to_aov_nodes
    return colortoaov


def color_aov_setup():
    color_to_aovs = get_color_to_aov()
    colorAov_list = []
    for aov_node in color_to_aovs:
        parms = aov_node.parms()
        i = 0
        for p in parms:

            if not p.isAtDefault():
                if p.name() == 'aov_name0':
                    if p.eval() != 'U_UVOBJP_uvobject':
                        aov_node.parm(p.name()).set('U_UVOBJP_uvobject')
                else:
                    if p.eval() != 'U_RGBAOV_rgbtoaov{i}'.format(i=i):
                        aov_node.parm(p.name()).set('U_RGBAOV_rgbtoaov{i}'.format(i=i))
                    i = i + 1
                if p.eval() not in colorAov_list:
                    colorAov_list.append(p.eval())
    return colorAov_list


def create_AO_shader():
    if not hou.node('/mat/aov_ao_mat'):
        mat = hou.node('/mat')
        rs_vopnet = mat.createNode('redshift_vopnet', 'aov_ao_mat')
        ao = rs_vopnet.createNode('redshift::AmbientOcclusion', 'AO')
        rs_material = rs_vopnet.node('redshift_material1')
        rs_material.setInput(0, ao)
    else:
        print('AO Shader Created')


def aov_setup():
    rops = get_rops()
    materials = get_all_materials()

    for rop in rops:
        # Default AOVs
        add_aov(rop, 'BUMPNORMALS', 'U_NORBMP_normalbump')
        add_aov(rop, 'Depth', 'U_DPTBSE_zdepth')
        add_aov(rop, 'SHADOWS', 'U_SHWBSE_shadow')
        add_aov(rop, 'DIFFUSE_TINT', 'U_DIFFIL_difFilter')
        add_aov(rop, 'World', 'U_WRDPOS_world')
        add_aov(rop, 'DIRECTLIGHTING_DIFFUSE', 'P_DIFLIT_diflit')

        # Add AOV based on Materials
        parms = get_changed_parms(materials)
        print(parms)
        for p in parms:
            if 'refl_' in str(p):
                add_aov(rop, 'INDIRECTLIGHTING_REFLECTIONS', 'P_RFLBSE_reflect')

            if 'refr_' in str(p):
                add_aov(rop, 'INDIRECTLIGHTING_REFRACTIONS', 'P_RFRBSE_refract')

            if 'ss_' in str(p) or 'ms_' in str(p):
                add_aov(rop, 'SSS', 'P_SSSBSE_subsurface')

            if 'emission_' in str(p):
                add_aov(rop, 'EMISSION', 'P_EMIBSE_emission')

            if 'absorption_' in str(p):
                add_aov(rop, 'VOLUMELIGHTING', 'P_VOLLIT_volumeLit')

        # GI check
        gi = rop.parm('RS_GIEnabled').eval()
        if gi > 0:
            add_aov(rop, 'GI', 'P_GILBSE_gi')

        # Caustic check
        caustics = rop.parm('PhotonCausticsEnable').eval()
        if caustics > 0:
            add_aov(rop, 'CAUSTICS', 'P_CAUBSE_caustics')

        # Color to AOV setup
        colorAov_list = color_aov_setup()
        if len(colorAov_list) > 0:
            for aov in colorAov_list:
                add_aov(rop, 'CUSTOM', aov)


def crypto_matte_setup():
    rops = get_rops()
    for rop in rops:
        matte = add_aov(rop, 'CRYPTOMATTE', 'U_CRYMAT_matte')
        obj = add_aov(rop, 'CRYPTOMATTE', 'U_CRYOBJ_matte')
        try:
            add_crypto(rop, 'U_CRYMAT_matte', matte)
            add_crypto(rop, 'U_CRYOBJ_matte', obj)
        except:
            pass


def ao_aov_setup():
    rops = get_rops()
    create_AO_shader()
    for rop in rops:
        ao = add_aov(rop, 'CUSTOM', 'U_AMBOCC_ao ')
        rop.parm('RS_aovCustomShader_{i}'.format(i=ao)).set('aov_ao_mat')


def motionVector_setup():
    rops = get_rops()
    for rop in rops:
        add_aov(rop, 2, 'U_MOVECT_motionVectors')
        try:
            rop.parm('MotionBlurEnabled').set(0)
        except:
            pass


class Ui_houdini_aov(object):
    def setupUi(self, houdini_aov):
        houdini_aov.setObjectName("houdini_aov")
        houdini_aov.resize(321, 540)
        self.main_ui = QtWidgets.QWidget(houdini_aov)
        self.main_ui.setObjectName("main_ui")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.main_ui)
        self.verticalLayout.setObjectName("verticalLayout")
        self.window = QtWidgets.QVBoxLayout()
        self.window.setObjectName("window")
        self.window_title = QtWidgets.QLabel(self.main_ui)
        self.window_title.setStyleSheet("font-weight: bold;\n"
                                        "font-size: 1.2em")
        self.window_title.setObjectName("window_title")
        self.window.addWidget(self.window_title)
        self.main_ui_layout = QtWidgets.QVBoxLayout()
        self.main_ui_layout.setObjectName("main_ui_layout")
        self.frame = QtWidgets.QFrame(self.main_ui)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                                           QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.aov_setup = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.aov_setup.sizePolicy().hasHeightForWidth())
        self.aov_setup.setSizePolicy(sizePolicy)
        self.aov_setup.setStyleSheet("QPushButton\n"
                                     "{\n"
                                     "border: none;\n"
                                     "color: black;\n"
                                     "background-color: #DCDCDC;\n"
                                     "font-weight: bold;\n"
                                     "}\n"
                                     "\n"
                                     "QPushButton:hover\n"
                                     "{\n"
                                     "background-color:#008B8B;\n"
                                     "color: white;\n"
                                     "}")
        self.aov_setup.setObjectName("aov_setup")
        self.aov_setup.clicked.connect(aov_setup)

        self.verticalLayout_2.addWidget(self.aov_setup)
        self.cryptomatte = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cryptomatte.sizePolicy().hasHeightForWidth())
        self.cryptomatte.setSizePolicy(sizePolicy)
        self.cryptomatte.setStyleSheet("QPushButton\n"
                                       "{\n"
                                       "border: none;\n"
                                       "color: black;\n"
                                       "background-color: #DCDCDC;\n"
                                       "font-weight: bold;\n"
                                       "}\n"
                                       "\n"
                                       "QPushButton:hover\n"
                                       "{\n"
                                       "background-color:#008B8B;\n"
                                       "color: white;\n"
                                       "}")
        self.cryptomatte.setObjectName("cryptomatte")
        self.cryptomatte.clicked.connect(crypto_matte_setup)

        self.verticalLayout_2.addWidget(self.cryptomatte)
        self.ao_setup = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ao_setup.sizePolicy().hasHeightForWidth())
        self.ao_setup.setSizePolicy(sizePolicy)
        self.ao_setup.setStyleSheet("QPushButton\n"
                                    "{\n"
                                    "border: none;\n"
                                    "color: black;\n"
                                    "background-color: #DCDCDC;\n"
                                    "font-weight: bold;\n"
                                    "}\n"
                                    "\n"
                                    "QPushButton:hover\n"
                                    "{\n"
                                    "background-color:#008B8B;\n"
                                    "color: white;\n"
                                    "}")
        self.ao_setup.setObjectName("ao_setup")
        self.ao_setup.clicked.connect(ao_aov_setup)

        self.verticalLayout_2.addWidget(self.ao_setup)
        self.motvector_setup = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.motvector_setup.sizePolicy().hasHeightForWidth())
        self.motvector_setup.setSizePolicy(sizePolicy)
        self.motvector_setup.setStyleSheet("QPushButton\n"
                                           "{\n"
                                           "border: none;\n"
                                           "color: black;\n"
                                           "background-color: #DCDCDC;\n"
                                           "font-weight: bold;\n"
                                           "}\n"
                                           "\n"
                                           "QPushButton:hover\n"
                                           "{\n"
                                           "background-color:#008B8B;\n"
                                           "color: white;\n"
                                           "}")
        self.motvector_setup.setObjectName("motvector_setup")
        self.motvector_setup.clicked.connect(motionVector_setup)

        self.verticalLayout_2.addWidget(self.motvector_setup)
        self.main_ui_layout.addWidget(self.frame)
        self.window.addLayout(self.main_ui_layout)
        self.verticalLayout.addLayout(self.window)
        houdini_aov.setCentralWidget(self.main_ui)
        houdini_aov.setWindowTitle("Houdini AOV")
        self.aov_setup.setText("AOV Setup")
        self.cryptomatte.setText("Cryptomatte Setup")
        self.ao_setup.setText("AO Setup")
        self.motvector_setup.setText("Motion Vetor Setup")
        self.window_title.setText("Houdini AOV Tools")


def set_up():
    set_rops()
    set_look_list()
    set_look_materials()
    set_all_materials()
    set_color_to_aov()


set_up()
houdini_aov = QtWidgets.QMainWindow()
ui = Ui_houdini_aov()
ui.setupUi(houdini_aov)
houdini_aov.show()
