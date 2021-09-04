// This file is a part of "Candle" application.
// Copyright 2015-2016 Hayrullin Denis Ravilevich

#include "tooldrawer.h"

ToolDrawer::ToolDrawer()
{
    m_toolDiameter = 3;
    m_toolLength = 15;
    m_toolPosition = QVector3D(0, 0, 0);
    m_rotationAngle = 0;
}


bool ToolDrawer::updateData()
{
    const int arcs = 2;

    // Clear data
    m_lines.clear();
    m_points.clear();

    // Prepare vertex
    VertexData vertex;
    vertex.color = Util::colorToVector(m_color);
    vertex.start = QVector3D(sNan, sNan, sNan);

	double x0  = m_toolPosition.x();  // short hand
	double y0  = m_toolPosition.y();
	double z0  = m_toolPosition.z();
	double d   = m_toolDiameter;
	double a   = m_toolAngle * M_PI / 180;

	// hack for lathe bit, if angle > 0 right-hand tool  (may want second color to high light
	
	vertex.position = QVector3D(x0,            y0, z0);            m_lines.append(vertex);
	vertex.position = QVector3D(x0 + d/tan(a), y0, z0 + d);        m_lines.append(vertex);

	vertex.position = QVector3D(x0 + d/tan(a),   y0, z0 + d);      m_lines.append(vertex);
	vertex.position = QVector3D(x0 + d/tan(a)+d, y0, z0 + d);      m_lines.append(vertex);

	vertex.position = QVector3D(x0 + d+d/tan(a), y0, z0 + d);      m_lines.append(vertex);
	vertex.position = QVector3D(x0 + d,          y0, z0);          m_lines.append(vertex);

	vertex.position = QVector3D(x0 + d, y0, z0);                   m_lines.append(vertex);
	vertex.position = QVector3D(x0,     y0, z0);                   m_lines.append(vertex);

	// assumes m_toolLength > d
	vertex.position = QVector3D(x0 + d, y0, z0);                   m_lines.append(vertex);	
	vertex.position = QVector3D(x0 + m_toolLength, y0, z0);        m_lines.append(vertex);
	
	vertex.position = QVector3D(x0 + m_toolLength, y0, z0+d);      m_lines.append(vertex);
	vertex.position = QVector3D(x0 + d+d/tan(a),   y0, z0+d);      m_lines.append(vertex);

								/*
    for (int i = 0; i < arcs; i++) {   // arcs=2 for flat lathe tool

		double ang = m_rotationAngle * M_PI/180  + i * 2*M_PI/arcs;
        double z   = m_toolPosition.z() + m_toolDiameter / 2 * cos(ang);
        double y   = m_toolPosition.y() + m_toolDiameter / 2 * sin(ang);

        // Side lines
        vertex.position = QVector3D(x0 + m_endLength,  y, z);        m_lines.append(vertex);
        vertex.position = QVector3D(x0 + m_toolLength, y, z);        m_lines.append(vertex);

        // Bottom lines  tool tip to side at endLength
        vertex.position = QVector3D(x0, y0, z0);                     m_lines.append(vertex);
        vertex.position = QVector3D(x0 + m_endLength, y, z);         m_lines.append(vertex);

        // Top lines
        vertex.position = QVector3D(x0 + m_toolLength, y0, z0);      m_lines.append(vertex);
        vertex.position = QVector3D(x0 + m_toolLength, y,  z );      m_lines.append(vertex);

        // Zero Z lines -> X  (projection to x=0) not very useful to me in lathe mode
        //vertex.position = QVector3D(0,  y0, z0);                     m_lines.append(vertex);
        //vertex.position = QVector3D(0,  y,  z);                      m_lines.append(vertex);
    }
								*/
								
    // Draw circles  Q: orientation ?
    // Bottom
    //m_lines += createCircle(QVector3D(m_toolPosition.x() + m_endLength, m_toolPosition.y(), m_toolPosition.z() ),
    //                        m_toolDiameter / 2, 20, vertex.color);

    // Top
    //m_lines += createCircle(QVector3D(m_toolPosition.x() + m_toolLength, m_toolPosition.y(), m_toolPosition.z()),
    //                        m_toolDiameter / 2, 20, vertex.color);

    // Zero Z circle  -> X
	// if (m_endLength == 0) {
    //    m_lines += createCircle( QVector3D(0, y0, z0), m_toolDiameter/2, 16, vertex.color);   // 16=arcs 
    //}

    return true;
}
QColor ToolDrawer::color() const
{
    return m_color;
}

void ToolDrawer::setColor(const QColor &color)
{
    m_color = color;
}


QVector<VertexData> ToolDrawer::createCircle(QVector3D center, double radius, int arcs, QVector3D color)
{
    // Vertices
    QVector<VertexData> circle;

    // Prepare vertex
    VertexData vertex;
    vertex.color = color;
    vertex.start = QVector3D(sNan, sNan, sNan);

    // Create line loop
    for (int i = 0; i <= arcs; i++) {
        double angle = 2 * M_PI * i / arcs;
        double x = center.x() + radius * cos(angle);
        double y = center.y() + radius * sin(angle);

        if (i > 1) {
            circle.append(circle.last());
        }
        else if (i == arcs) circle.append(circle.first());

        vertex.position = QVector3D(x, y, center.z());
        circle.append(vertex);
    }

    return circle;
}

double ToolDrawer::toolDiameter() const
{
    return m_toolDiameter;
}

void ToolDrawer::setToolDiameter(double toolDiameter)
{
    if (m_toolDiameter != toolDiameter) {
        m_toolDiameter = toolDiameter;
        update();
    }
}
double ToolDrawer::toolLength() const
{
    return m_toolLength;
}

void ToolDrawer::setToolLength(double toolLength)
{
    if (m_toolLength != toolLength) {
        m_toolLength = toolLength;
        update();
    }
}
QVector3D ToolDrawer::toolPosition() const
{
    return m_toolPosition;
}

void ToolDrawer::setToolPosition(const QVector3D &toolPosition)
{
    if (m_toolPosition != toolPosition) {
        m_toolPosition = toolPosition;
        update();
    }
}
double ToolDrawer::rotationAngle() const
{
    return m_rotationAngle;
}

void ToolDrawer::setRotationAngle(double rotationAngle)
{
    if (m_rotationAngle != rotationAngle) {
        m_rotationAngle = rotationAngle;
        update();
    }
}

void ToolDrawer::rotate(double angle)
{
    setRotationAngle(normalizeAngle(m_rotationAngle + angle));
}

double ToolDrawer::toolAngle() const
{
    return m_toolAngle;
}

void ToolDrawer::setToolAngle(double toolAngle)
{
    if (m_toolAngle != toolAngle) {
        m_toolAngle = toolAngle;

        m_endLength = m_toolAngle > 0 && m_toolAngle < 180 ? m_toolDiameter / 2 / tan(m_toolAngle / 180 * M_PI / 2) : 0;
        if (m_toolLength < m_endLength) m_toolLength = m_endLength;

        update();
    }
}

double ToolDrawer::normalizeAngle(double angle)
{
    while (angle < 0) angle += 360;
    while (angle > 360) angle -= 360;
    
    return angle;
}
