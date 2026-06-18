export const EMPTY_USER = {
  username: "",
  full_name: "",
  national_id: "",
  city: "",
};

export function emptyMainEquipo() {
  return {
    id: 1,
    equipment_type: "Laptop",
    quantity: 1,
    manufacturer: "Lenovo",
    model: "",
    serial_number: "",
    purchase_cost: 0,
    status: "Nuevo",
    hostname: "",
    observation: "",
    location: "BODEGA GYE",
  };
}

export const ACCESORIO_DEFAULTS = {
  Diadema: { manufacturer: "Poly", model: "Blackwire 3320", purchase_cost: 62, quantity: 1 },
  Cargador: { manufacturer: "Lenovo", model: "Genérico", purchase_cost: 100, quantity: 1 },
  Mochila: { manufacturer: "Targus", model: "Genérico", purchase_cost: 30, quantity: 1 },
  Monitor: { manufacturer: "LG", purchase_cost: 70, quantity: 1 },
  Teclado: { manufacturer: "Lenovo", purchase_cost: 20, quantity: 1 },
  Mouse: { manufacturer: "Lenovo", purchase_cost: 20, quantity: 1 },
  Otros: { manufacturer: "", model: "", purchase_cost: 0, quantity: 1 },
};

export const ACCESORIO_TYPES = ["Diadema", "Cargador", "Mochila", "Monitor", "Teclado", "Mouse", "Otros"];
