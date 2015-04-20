import logging
import numpy as np
import ctypes
import sys
import math

from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QSize
from PyQt5.QtGui import QColor, QMatrix4x4, QVector3D, QQuaternion
from PyQt5.QtOpenGL import QGLWidget

import OpenGL
OpenGL.ERROR_CHECKING = True
OpenGL.FULL_LOGGING = True
from OpenGL.GL import *


class Simulator(QGLWidget):
    xRotationChanged = pyqtSignal(int)
    yRotationChanged = pyqtSignal(int)
    zRotationChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(Simulator, self).__init__(parent)
        print(glGetString(GL_EXTENSIONS))
        
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
        
        self.xPan = 0
        self.yPan = 0
        self.zPan = -10
        
        self.colors = [ (1,0,0,1) ]
        self.positions = [ (0,0) ]
        self._linecount = len(self.positions)
        
        self.data = np.zeros(self._linecount, [("position", np.float32, 2), ("color",    np.float32, 4)])
        self.data['color']    = self.colors
        self.data['position'] = self.positions
        
        self.lastPos = QPoint()
        
        self.width = 100
        self.height = 100
        self.model_rotation = 0
        
        self.draw_grid()


    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(400, 400)

    def initializeGL(self):
        
        print("OPENGL VERSION", glGetString(GL_VERSION))
        print("OPENGL VENDOR", glGetString(GL_VENDOR))
        print("OPENGL RENDERER", glGetString(GL_RENDERER))
        print("OPENGL GLSL VERSION", glGetString(GL_SHADING_LANGUAGE_VERSION))
        
        self.program  = glCreateProgram()
        vertex   = glCreateShader(GL_VERTEX_SHADER)
        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        
        # Set shaders source
        with open("vertex.c", "r") as f: vertex_code = f.read()
        with open("fragment.c", "r") as f: fragment_code = f.read()
        glShaderSource(vertex, vertex_code)
        glShaderSource(fragment, fragment_code)
        
        # Compile shaders
        glCompileShader(vertex)
        glCompileShader(fragment)
        
        glAttachShader(self.program, vertex)
        glAttachShader(self.program, fragment)
        
        glLinkProgram(self.program)
        
        glDetachShader(self.program, vertex)
        glDetachShader(self.program, fragment)
        
        glUseProgram(self.program)
        
        # Request a buffer_label slot from GPU
        self.buffer_label = glGenBuffers(1)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer_label)

        glEnable (GL_LINE_SMOOTH)
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glHint (GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
        glLineWidth (1)
        
        
    def wipe(self):
        self.colors = []
        self.positions = []
        
        
    def add_vertex(self, tuple):
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, None, GL_DYNAMIC_DRAW) #https://www.opengl.org/wiki/Buffer_Object_Streaming#Buffer_update
        
        tuple = (tuple[0], tuple[1])
        self.positions.append(tuple)
        self.colors.append((1, 1, 1, 1))
        self._linecount = len(self.positions)
        
        self.data = np.zeros(self._linecount, [("position", np.float32, 2), ("color",    np.float32, 4)])
        self.data['color']    = self.colors
        self.data['position'] = self.positions
        
    def _setup_buffer(self):
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, self.data, GL_DYNAMIC_DRAW)
        
        stride = self.data.strides[0]
        
        offset = ctypes.c_void_p(0)
        loc = glGetAttribLocation(self.program, "position")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer_label)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

        offset = ctypes.c_void_p(self.data.dtype["position"].itemsize)
        loc = glGetAttribLocation(self.program, "color")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer_label)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, stride, offset)
        
        #loc = glGetUniformLocation(self.program, "scale")
        #glUniform1f(loc, 0.01)
        
        # MODEL MATRIX BEGIN ==========
        qu_rot = QQuaternion.fromAxisAndAngle(0, 0, 1, self.model_rotation)
        mat_m = QMatrix4x4()
        #mat_m.rotate(self.model_rotation, QVector3D(0, 1, 0))
        mat_m.rotate(qu_rot)
        mat_m = self.qt_mat_to_array(mat_m)
        loc_mat_m = glGetUniformLocation(self.program, "mat_m")
        glUniformMatrix4fv(loc_mat_m, 1, GL_TRUE, mat_m)
        # MODEL MATRIX END ==========
        
        # VIEW MATRIX BEGIN ==========
        mat_v = QMatrix4x4()
        mat_v.lookAt(QVector3D(2, 2, 2), QVector3D(0, 0, 0), QVector3D(0, 0, 1))
        mat_v = self.qt_mat_to_array(mat_v)
        loc_mat_v = glGetUniformLocation(self.program, "mat_v")
        glUniformMatrix4fv(loc_mat_v, 1, GL_TRUE, mat_v)
        # VIEW MATRIX END ==========
        
        # PROJECTION MATRIX BEGIN ==========
        aspect = self.width / self.height
        mat_p = QMatrix4x4()
        mat_p.perspective(45, aspect, 1, 100)
        mat_p = self.qt_mat_to_array(mat_p)
        loc_mat_p = glGetUniformLocation(self.program, "mat_p")
        glUniformMatrix4fv(loc_mat_p, 1, GL_TRUE, mat_p)
        # PROJECTION MATRIX END ==========
        
        # MVP MATRIX BEGIN =====
        #mvp_matrix = QMatrix4x4()
        #mvp_matrix = mat_m
        #mvp_matrix = self.qt_mat_to_array(mvp_matrix)
        
        #loc_mvp_matrix = glGetUniformLocation(self.program, "mvp_matrix")
        #glUniformMatrix4fv(loc_mvp_matrix, 1, GL_TRUE, mvp_matrix)
        # MVP MATRIX END =====
        


    def paintGL(self):
        #print("paintGL")
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)        
        self._setup_buffer()
        glDrawArrays(GL_LINE_STRIP, 0, self._linecount)
        # swapping buffer automatically by Qt


    def resizeGL(self, width, height):
        print("resizeGL")
        self.width = width
        self.height = height
        
        glViewport(0, 0, width, height)
        
       
        
        
    def setXRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle
            self.xRotationChanged.emit(angle)
            #self.updateGL()

    def setYRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle
            self.yRotationChanged.emit(angle)
            #self.updateGL()

    def setZRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle
            self.zRotationChanged.emit(angle)
            #self.updateGL()
            
    def setXPan(self, val):
        if val != self.xPan:
            self.xPan = val / 1000.0
            
    def setYPan(self, val):
        if val != self.yPan:
            self.yPan = val / 1000.0
            
    def setZPan(self, val):
        if val != self.zPan:
            self.zPan = val / 1000.0

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.LeftButton:
            self.setXRotation(self.xRot + 8 * dy)
            self.setYRotation(self.yRot + 8 * dx)
        elif event.buttons() & Qt.RightButton:
            self.setXRotation(self.xRot + 8 * dy)
            self.setZRotation(self.zRot + 8 * dx)

        self.lastPos = event.pos()
        
    def normalizeAngle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle
    
    def draw_grid(self):
        #self.add_vertex((0, 0))
        #self.add_vertex((1000, 1000))
        #self.add_vertex((9.9, 9.9))
        #self.add_vertex((-9.9, -9.9))
        #return
        for i in range(10):
            dir = 1 if (i % 2) == 0 else -1
            self.add_vertex((i/10, 0.1 * dir))
            self.add_vertex((0.1 + i/10, 0.1 * dir))
        
    def qt_mat_to_array(self, mat):
        #arr = [[0 for x in range(4)] for x in range(4)]
        arr = [0] * 16
        for i in range(4):
            for j in range(4):
                idx = 4 * i + j
                arr[idx] = mat[i, j]
        return arr
        