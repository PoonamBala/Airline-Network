import math
import vtk

def latlon_to_xyz(lat, lon, R=1.0):
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    x = R * math.cos(lat_r) * math.cos(lon_r)
    y = R * math.cos(lat_r) * math.sin(lon_r)
    z = R * math.sin(lat_r)
    return (x, y, z)

def build_earth(radius=1.0):
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius)
    sphere.SetThetaResolution(64)
    sphere.SetPhiResolution(64)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphere.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.08, 0.10, 0.25)
    return actor

def build_airport_glyphs(airports_df, centrality_lookup, R=1.02):
    points = vtk.vtkPoints()
    bet_scalars = vtk.vtkFloatArray(); bet_scalars.SetName("bet_cent")
    radii = vtk.vtkFloatArray(); radii.SetName("radius")

    for _, row in airports_df.iterrows():
        ap = row["IATA_CODE"]; lat, lon = row["LAT"], row["LON"]
        x,y,z = latlon_to_xyz(lat, lon, R)
        points.InsertNextPoint(x,y,z)
        bet = float(centrality_lookup.get(ap, {}).get("bet_cent", 0.0))
        deg = float(centrality_lookup.get(ap, {}).get("deg_cent", 0.0))
        bet_scalars.InsertNextValue(bet)
        radii.InsertNextValue(0.01 + 0.05 * deg)

    p = vtk.vtkPolyData(); p.SetPoints(points)
    p.GetPointData().AddArray(bet_scalars)
    p.GetPointData().AddArray(radii)

    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(1.0); sphere.SetThetaResolution(24); sphere.SetPhiResolution(24)

    glyph = vtk.vtkGlyph3D()
    glyph.SetSourceConnection(sphere.GetOutputPort())
    glyph.SetInputData(p)
    glyph.ScalingOn()
    glyph.SetScaleModeToScaleByScalar()
    glyph.SetInputArrayToProcess(0, 0, 0, 0, "radius")

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(glyph.GetOutputPort())
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SelectColorArray("bet_cent")
    lut = vtk.vtkLookupTable(); lut.SetNumberOfTableValues(256); lut.Build()
    mapper.SetLookupTable(lut)
    rng = bet_scalars.GetRange(); mapper.SetScalarRange(rng[0], max(rng[1], rng[0]+1e-6))

    actor = vtk.vtkActor(); actor.SetMapper(mapper)
    return actor

def build_route_lines(routes_df, coord_lookup, R=1.0):
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    delays = vtk.vtkFloatArray(); delays.SetName("avg_delay")

    for _, r in routes_df.iterrows():
        u, v = r["ORIGIN"], r["DEST"]
        if u not in coord_lookup or v not in coord_lookup:
            continue
        lat1, lon1 = coord_lookup[u]; lat2, lon2 = coord_lookup[v]
        x1,y1,z1 = latlon_to_xyz(lat1, lon1, R)
        x2,y2,z2 = latlon_to_xyz(lat2, lon2, R)
        id1 = points.InsertNextPoint(x1,y1,z1)
        id2 = points.InsertNextPoint(x2,y2,z2)
        line = vtk.vtkLine(); line.GetPointIds().SetId(0, id1); line.GetPointIds().SetId(1, id2)
        lines.InsertNextCell(line)
        delays.InsertNextValue(float(r.get("avg_arr_delay", 0.0)))

    poly = vtk.vtkPolyData()
    poly.SetPoints(points); poly.SetLines(lines)
    poly.GetCellData().AddArray(delays)
    poly.GetCellData().SetActiveScalars("avg_delay")

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    mapper.SetScalarModeToUseCellFieldData()
    mapper.SelectColorArray("avg_delay")
    rng = delays.GetRange()
    mapper.SetScalarRange(rng[0], max(rng[1], rng[0]+1e-6))

    lut = vtk.vtkLookupTable()
    lut.SetNumberOfTableValues(256); lut.Build()
    mapper.SetLookupTable(lut)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(0.5)
    actor.GetProperty().SetLineWidth(2.0)
    return actor
