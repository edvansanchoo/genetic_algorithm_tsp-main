export interface StateUpdate {
  type: "state_update";
  generation: number;
  running: boolean;
  metrics: {
    fitness: number;
    distance: number;
    priority_penalty: number;
    blocked_penalty: number;
    population_size: number;
    fps: number;
    total_cost: number;
    priority_served_pct: number;
  };
  params: {
    mutation: number;
    priority_weight: number;
    vehicle_count: number;
    capacity: number;
    transit_count: number;
    param_ranges: Record<string, [number, number]>;
  };
  toggles: {
    two_opt: boolean;
    show_mesh: boolean;
  };
  focus: {
    vehicle_id: number | null;
    trip_index: number | null;
  };
  summary: {
    vehicles_active: number;
    vehicles_total: number;
    capacity_total: number;
    deliveries_done: number;
    deliveries_total: number;
    trips_total: number;
    blocked_nodes: number;
  };
  display: {
    vehicle_colors_ui: string[];
    elite_pct: number;
  };
  map: {
    bounds: [number, number, number, number];
    depot: [number, number] | null;
    deliveries: Array<{
      id: string;
      x: number;
      y: number;
      priority: number;
      demand: number;
      color: string;
    }>;
    mesh: {
      edges: number[][];
      transit_nodes: number[][];
      blocked: number[][];
    };
    theme: Record<string, string | string[]>;
  };
  plans: Record<
    string,
    {
      distance: number;
      load: number;
      capacity: number;
      fitness: number;
      priority_penalty: number;
      trips: Array<{
        index: number;
        stops: string[];
        load: number;
        polylines: number[][][];
      }>;
    }
  >;
  runner_up: StateUpdate["plans"];
  histories: Record<string, number[]>;
  animation: {
    vehicle_id: number;
    position: [number, number];
    trip_index: number | null;
  } | null;
  routes_panel: Array<{
    type: "header" | "trip";
    text: string;
    vehicle_id?: number;
    trip_index?: number;
  }>;
  logs: Array<{ ts: string; type: string; message: string }>;
}

export interface HistoryEntry {
  generation: number;
  fitness: number;
  distance: number;
  priority_penalty: number;
}
