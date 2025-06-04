# Copyright © 2025 Brandon Namgoong.
# Licensed under the GNU General Public License v3.0.
# Made for ICS3U1.

"""
Module containing all functions regarding rendering using OpenGL,
and creating and interacting with offsite, hidden OpenGL contexts via glfw.

Some code has been adapted from kickstart ideas from GPT 4o. (OpenGL is horrifying for beginners)
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from platform import system
import numpy as np
import ctypes
import sys

from utils import unifiedPath

# preloads the GLFW library
if hasattr(sys, '_MEIPASS'):
    if system() == "Windows": # windows
        libglfwPath = unifiedPath("glfw3/glfw3.dll") # add to subfolder
    elif system() == "Darwin": # macOS
        libglfwPath = unifiedPath("libglfw.3.dylib")
    ctypes.CDLL(str(libglfwPath))
import glfw

#-----------------------------------------------------------------------------
# globals
#-----------------------------------------------------------------------------

# screen dimensions
__screenWidth                     = 0 # placeholder
__screenHeight                    = 0 # placeholder

# all window hints needed during init except hiding
__windowHints: dict               = {
    glfw.CONTEXT_VERSION_MAJOR: 2, # OpenGL version 2.1 because 3.0+ overcomplicates things and only 3.2 or 2.1 available on macOS
    glfw.CONTEXT_VERSION_MINOR: 1,
    glfw.RED_BITS: 8,
    glfw.GREEN_BITS: 8,
    glfw.BLUE_BITS: 8,
    glfw.ALPHA_BITS: 8
}

__boxScale: float                 = 1 / 120 # box is approx 1/60 of screen dimensions

# OpenGL capabilities to be enabled
__glCapabilities: list            = [
    GL_NORMALIZE, GL_CULL_FACE, GL_DEPTH_TEST,  # normalize vectors, do face culling, enable depth clipping
    GL_LIGHTING, GL_COLOR_MATERIAL,             # enable lighting and colored materials
    GL_LIGHT0, GL_LIGHT1                        # enable lights 0 and 1
]

# lighting
__light0Pos: list[float]          = [-10.0, -10.0, 0.0, 1.0] # behind left light for shapes
__light1Pos: list[float]          = [0.0, 0.0, 10.0, 0.0] # direct light towards top of shapes
__lightDiffuse: list[float]       = lambda strength : [strength, strength, strength, 1.0]

#-----------------------------------------------------------------------------
# objects
#-----------------------------------------------------------------------------

__window: glfw._GLFWwindow  = None # placeholder for when window is created

#-----------------------------------------------------------------------------
# private functions
#-----------------------------------------------------------------------------

# Calculates and returns a matrix representing the normal vector of the specified face
def __getNormal(face: tuple[int, ...], vertexArray: list[tuple[float, float, float]]) -> tuple[float]:
    netNormal = np.array([0.0, 0.0, 0.0]) # start with empty vector
    # run through and summate every pair
    for i in range(len(face)):
        netNormal += np.cross(
            np.array(vertexArray[face[(i + 1) % len(face)]]) - np.array(vertexArray[face[i]]),                   # current vector line
            np.array(vertexArray[face[(i + 2) % len(face)]]) - np.array(vertexArray[face[(i + 1) % len(face)]])  # vector line ahead
        )
    return tuple((netNormal / np.linalg.norm(netNormal)).tolist())

# Renders the given concave face using tessellation as a continous, filled polygon
def __tessellate(face: tuple[int, ...], vertexArray: list[tuple[float, float, float]]):
    # setup
    tess: GLUtesselator = gluNewTess()
    gluTessCallback(tess, GLU_TESS_BEGIN, glBegin)
    gluTessCallback(tess, GLU_TESS_END, glEnd)
    gluTessCallback(tess, GLU_TESS_VERTEX, glVertex3dv)
    gluTessCallback(tess, GLU_TESS_COMBINE, lambda coordinates : coordinates)
    gluTessBeginPolygon(tess, None)
    gluTessBeginContour(tess)

    # tessellate
    for vertexIndex in face:
        coord = (GLdouble * 3)(*vertexArray[vertexIndex]) # "convert to C-style arrays required by GLU" apparently
        gluTessVertex(tess, coord, coord)
    
    # end
    gluTessEndContour(tess)
    gluTessEndPolygon(tess)
    gluDeleteTess(tess)

#-----------------------------------------------------------------------------
# public functions
#-----------------------------------------------------------------------------

def init(
    width: int, height: int,
    offsetY: int = 0,
    isHidden: bool = True
):
    """
    Initializes an offsite OpenGL context with the specified window width and height.
    `offsetY` is an optional parameter that moves the entire viewport +Y units.

    By default `isHidden` is set to `True`, and should be kept that way.
    If the window must be visible, set `isHidden` to `False`.
    
    Should be called just once to initialize glfw and OpenGL.
    """
    # first initialize glfw
    glfw.init()

    # configure window settings
    if isHidden:
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE) # hide window
    for key in __windowHints.keys():
        glfw.window_hint(key, __windowHints[key])
    
    # create and set window
    global __window ; __window = glfw.create_window(width, height, "Hidden OpenGL context", None, None)
    glfw.make_context_current(__window) # ensure correct OpenGL context

    # initialize OpenGL
    glMatrixMode(GL_PROJECTION) # load projection matrix stack
    glLoadIdentity() # flush projection matrix

    scaledWidth = width * __boxScale
    scaledHeight = height * __boxScale

    glOrtho( # set orthographic projection to box
        -scaledWidth, scaledWidth,
        -scaledHeight + offsetY, scaledHeight + offsetY,
        -50, 50 # arbitrary depth
    )
    glMatrixMode(GL_MODELVIEW) # load modelview matrix stack
    glLoadIdentity() # flush modelview matrix

    # enable capabilities
    for cap in __glCapabilities: glEnable(cap)

    glCullFace(GL_BACK) # culling set to back-face
    
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # store screen dimensions
    global __screenWidth, __screenHeight ; __screenWidth, __screenHeight = width, height

def setupScene(xtheta: float = -45.0):
    """
    Sets up the scene with a worldview rotation and lights.
    Must be called periodically per loop pre-rendering, after a `flush()`.

    `xtheta` specifies the angle in degrees about the origin after translation.
    By default it is 45º clockwise for isometric projection.
    """
    # set a worldview tilt
    glRotated(xtheta, 1, 0, 0)

    # setup lights
    glLightfv(GL_LIGHT0, GL_POSITION, __light0Pos) # LIGHT0
    glLightfv(GL_LIGHT0, GL_DIFFUSE, __lightDiffuse(0.5))

    glLightfv(GL_LIGHT1, GL_POSITION, __light1Pos) # LIGHT1
    glLightfv(GL_LIGHT1, GL_DIFFUSE, __lightDiffuse(1.0))

def drawWireframe(
    vertexArray: list[tuple[float, float, float]], lineArray: list[tuple[int, int]],
    vertexCol: tuple[int, int, int], lineCol: tuple[int, int, int],
    vertexDiameter: int = 8, lineWidth: int = 2,
    dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
    theta: float = 0.0
):
    """
    Renders the given set of vertices as a wireframe of vertices and lines.

    `vertexArray` specifies the set of vertices and `lineArray` specifies the set of lines.
    `vertexCol` and `lineCol` values range from `0` to `255`.
    The default vertex diameter is 8 pixels and the default line width is 2 pixels.
    Translate using projection units `dx` in +X, `dy` in +Y, and `dz` in +Z.
    `theta` intrinsically rotates in degrees about z-axis.
    """
    glPushMatrix() # saves current stack

    # apply transformations
    glTranslated(dx, dy, dz)
    glRotated(theta, 0, 0, 1)

    # line rendering FIRST
    glColor3d(
        lineCol[0] / 255, lineCol[1] / 255, lineCol[2] / 255 # normalize to 0 - 1 range
    )
    glLineWidth(lineWidth)
    glBegin(GL_LINES)
    for line in lineArray: # draw each line
        for vertexIndex in line:
            glVertex3dv(vertexArray[vertexIndex])
    glEnd()

    # vertex rendering
    glColor3d(
        vertexCol[0] / 255, vertexCol[1] / 255, vertexCol[2] / 255
    )
    glPointSize(vertexDiameter)
    glBegin(GL_POINTS)
    for vertex in vertexArray: # draw each vertex
        glVertex3dv(vertex)
    glEnd()

    glPopMatrix() # restores previous stack

def drawPolygon(
    vertexArray: list[tuple[float, float, float]],
    baseArray: list[tuple[int, ...]], quadArray: list[tuple[int, int, int, int]],
    isConvex: bool,
    avgColor: tuple[int, int, int],
    dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
    theta: float = 0.0
):
    """
    Renders the given set of faces as a continuous, filled polygon.

    `vertexArray` specifies the set of vertices,
    `baseArray` specifies the set of base faces, and `quadArray` specifies the set of quad faces.
    This rendering involves simple shading with respect to each face.
    `isConvex` specifies whether the base polygon is convex or not.
    `avgColor` specifies the base color that shading will use to make certain faces darker or lighter.
    Its values range from `0` to `255`.
    Translate using projection units `dx` in +X, `dy` in +Y, and `dz` in +Z.
    `theta` intrinsically rotates in degrees about z-axis.
    """
    glPushMatrix() # saves current stack

    # apply transformations
    glTranslated(dx, dy, dz)
    glRotated(theta, 0, 0, 1)

    # set color
    glColor3d(
        avgColor[0] / 255, avgColor[1] / 255, avgColor[2] / 255
    )

    # render bases
    if isConvex:
        for face in baseArray:
            glBegin(GL_POLYGON)
            glNormal3dv(
                __getNormal(face, vertexArray) # define the normal for each face
            )
            for vertexIndex in face:
                glVertex3dv(vertexArray[vertexIndex])
            glEnd()
    else: # tessellation time
        for face in baseArray:
            glNormal3dv(
                __getNormal(face, vertexArray)
            )
            __tessellate(face, vertexArray)

    # render quads
    glBegin(GL_QUADS)
    for face in quadArray:
        glNormal3dv(
            __getNormal(face, vertexArray)
        )
        for vertexIndex in face:
            glVertex3dv(vertexArray[vertexIndex])
    glEnd()

    glPopMatrix() # restores previous stack

def getMatrix(
    dx: float, dy: float, dz: float,
    theta: float
) -> list:
    "Calculates and returns the modelview matrix for the given transformations."
    glPushMatrix() # saves current stack

    # apply transformations
    glTranslated(dx, dy, dz)
    glRotated(theta, 0, 0, 1)

    mat = glGetDoublev(GL_MODELVIEW_MATRIX) # get matrix

    glPopMatrix() # restores previous stack

    return mat

def toBytes():
    "Returns the OpenGL thread frame matrix as raw byte data."
    glPixelStorei(GL_PACK_ALIGNMENT, 1) # set pixel storage mode
    glReadBuffer(GL_FRONT)
    glFinish()
    
    # get pixel array
    return np.frombuffer(
        buffer = glReadPixels(0, 0, __screenWidth, __screenHeight, GL_RGBA, GL_UNSIGNED_BYTE),
        dtype = np.uint8
    ).reshape( # reshape into proper shape
        (__screenHeight, __screenWidth, 4)
    ).tobytes()

def reset():
    """
    Sets transparent background and clears OpenGL buffers and matrix stack.
    
    Must be called periodically at the start of loops.
    """
    glfw.make_context_current(__window) # ensure correct OpenGL context
    glViewport(0, 0, __screenWidth, __screenHeight)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT) # clear buffers
    glLoadIdentity() # load identity matrix

def finish():
    """
    Signals the OpenGL context that rendering of the current frame (or iteration of loop) is complete.

    Must be called periodically in loops after all render commands.
    """
    glfw.swap_buffers(__window) # rotate back buffer to front buffer

def end():
    "Ends the current glfw OpenGL context."
    glfw.destroy_window(__window)
    glfw.terminate()