#include "origindrawer.h"

OriginDrawer::OriginDrawer()
{
}

// remove rectangular, dim axis color from 1.0 to 
bool OriginDrawer::updateData()
{
    m_lines = {
        // X-axis, rotate arrow head to x/z plane
        {QVector3D(0, 0, 0), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(9, 0, 0), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(10, 0, 0), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(8,  0, 0.3), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(8,  0, 0.3), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(8,  0, -0.3), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(8,  0, -0.3), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(10, 0, 0), QVector3D(0.3, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},

        // Y-axis
        {QVector3D(0, 0, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0, 9, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0, 10, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0.3, 8, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0.3, 8, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-0.3, 8, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-0.3, 8, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0, 10, 0), QVector3D(0.0, 0.3, 0.0), QVector3D(sNan, sNan, sNan)},

        // Z-axis
        {QVector3D(0, 0, 0), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0, 0, 9), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0, 0, 10), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0.3, 0, 8), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0.3, 0, 8), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-0.3, 0, 8), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-0.3, 0, 8), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},
        {QVector3D(0, 0, 10), QVector3D(0.0, 0.0, 0.3), QVector3D(sNan, sNan, sNan)},

        // 2x2 rect
		/*        {QVector3D(1, 1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-1, 1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-1, 1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-1, -1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(-1, -1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(1, -1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(1, -1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
        {QVector3D(1, 1, 0), QVector3D(1.0, 0.0, 0.0), QVector3D(sNan, sNan, sNan)},
		*/
    };
    return true;
}
