import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authFetch } from "../api/api";

export default function Quotations() {

  const navigate = useNavigate();

  const [clients, setClients] = useState([]);
  const [cities, setCities] = useState([]);
  const [services, setServices] = useState([]);
  const [vendors, setVendors] = useState([]);

  const [selectedClient, setSelectedClient] = useState("");
  const [margin, setMargin] = useState(25);

  const emptyRow = {
    city_id: "",
    category: "",
    service_id: "",
    vendor_id: "",
    cost_price: "",
    manual_margin_percentage: "",
    start_date: "",
    end_date: "",
    quantity: 1
  };

  const [items, setItems] = useState([{ ...emptyRow }]);

  // ================= LOAD INITIAL =================
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [cRes, cityRes, sRes, vRes] = await Promise.all([
        authFetch("/clients/"),
        authFetch("/cities/"),
        authFetch("/services/"),
        authFetch("/vendors/")
      ]);

      setClients(await cRes.json());
      setCities(await cityRes.json());
      setServices(await sRes.json());
      setVendors(await vRes.json());

    } catch (err) {
      console.error("Initial Load Error:", err);
    }
  };

  // ================= FILTER SERVICES =================
  const filteredServices = (cityId, category) => {
    return services.filter(
      s =>
        String(s.city_id) === String(cityId) &&
        s.category?.toUpperCase() === category?.toUpperCase()
    );
  };

  // ================= UPDATE FIELD =================
  const updateField = (index, field, value) => {
    const updated = [...items];
    updated[index][field] = value;

    if (field === "city_id") {
      updated[index] = {
        ...emptyRow,
        city_id: value
      };
    }

    if (field === "category") {
      updated[index].service_id = "";
    }

    if (field === "start_date" || field === "end_date") {
      const start = new Date(updated[index].start_date);
      const end = new Date(updated[index].end_date);

      if (!isNaN(start) && !isNaN(end) && end > start) {
        const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        updated[index].quantity = diff;
      }
    }

    setItems(updated);
  };

  const removeRow = (index) => {
    const updated = [...items];
    updated.splice(index, 1);
    setItems(updated);
  };

  const addNewRow = () => {
    setItems([...items, { ...emptyRow }]);
  };

  // ================= CALCULATIONS =================
  const calculateRow = (item) => {
    const cost = Number(item.cost_price) || 0;
    const qty = Number(item.quantity) || 0;

    const rowMargin =
      item.manual_margin_percentage !== ""
        ? Number(item.manual_margin_percentage)
        : margin;

    const sellUnit = cost + (cost * rowMargin / 100);
    const totalCost = cost * qty;
    const totalSell = sellUnit * qty;
    const profit = totalSell - totalCost;

    return { totalCost, totalSell, profit };
  };

  const totals = items.reduce((acc, item) => {
    const row = calculateRow(item);
    acc.cost += row.totalCost;
    acc.sell += row.totalSell;
    acc.profit += row.profit;
    return acc;
  }, { cost: 0, sell: 0, profit: 0 });

  // ================= SAVE QUOTATION =================
  const saveQuotation = async () => {

    if (!selectedClient) {
      alert("Select Client");
      return;
    }

    const validItems = items.filter(i =>
      i.service_id &&
      i.cost_price &&
      i.start_date &&
      i.end_date &&
      Number(i.quantity) > 0
    );

    if (validItems.length === 0) {
      alert("Add at least one valid service row");
      return;
    }

    const payload = {
      client_id: Number(selectedClient),
      margin_percentage: margin,
      items: validItems.map(i => ({
        service_id: Number(i.service_id),
        vendor_id: i.vendor_id ? Number(i.vendor_id) : null,
        cost_price: Number(i.cost_price),
        quantity: Number(i.quantity),
        start_date: i.start_date,
        end_date: i.end_date,
        manual_margin_percentage:
          i.manual_margin_percentage !== ""
            ? Number(i.manual_margin_percentage)
            : null
      }))
    };

    try {
      const res = await authFetch("/quotations/", {
        method: "POST",
        body: payload
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "Error saving quotation");
        return;
      }

      const data = await res.json();
      navigate(`/quotation/${data.id}`);

    } catch (err) {
      console.error("Save error:", err);
      alert("Server connection error");
    }
  };

  // ================= UI =================
  return (
    <div className="flex bg-gray-100 min-h-screen">

      <div className="w-3/4 p-8">

        <h1 className="text-3xl font-bold mb-6">
          Create Quotation
        </h1>

        <div className="bg-white p-6 rounded-xl shadow mb-6 grid grid-cols-2 gap-6">

          <div>
            <label className="block mb-1 font-semibold">Client</label>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className="border p-2 rounded w-full"
            >
              <option value="">Select Client</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>
                  {c.company_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block mb-1 font-semibold">Global Margin %</label>
            <input
              type="number"
              value={margin}
              min="0"
              className="border p-2 rounded w-full"
              onChange={(e) => setMargin(Number(e.target.value))}
            />
          </div>

        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          {items.map((item, index) => {

            const row = calculateRow(item);

            return (
              <div key={index} className="grid grid-cols-10 gap-2 mb-2 text-sm">

                <select
                  value={item.city_id}
                  onChange={(e) => updateField(index, "city_id", e.target.value)}
                  className="border p-1 rounded"
                >
                  <option value="">City</option>
                  {cities.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>

                <select
                  value={item.category}
                  onChange={(e) => updateField(index, "category", e.target.value)}
                  className="border p-1 rounded"
                >
                  <option value="">Type</option>
                  <option value="HOTEL">Hotel</option>
                  <option value="TOUR">Tour</option>
                  <option value="TRANSFER">Transfer</option>
                  <option value="VISA">Visa</option>
                  <option value="TICKET">Ticket</option>
                </select>

                <select
                  value={item.service_id}
                  onChange={(e) => updateField(index, "service_id", e.target.value)}
                  className="border p-1 rounded"
                >
                  <option value="">Service</option>
                  {filteredServices(item.city_id, item.category).map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>

                <select
                  value={item.vendor_id}
                  onChange={(e) => updateField(index, "vendor_id", e.target.value)}
                  className="border p-1 rounded"
                >
                  <option value="">Vendor</option>
                  {vendors.map(v => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                </select>

                <input
                  type="number"
                  placeholder="Cost"
                  value={item.cost_price}
                  onChange={(e) => updateField(index, "cost_price", e.target.value)}
                  className="border p-1 rounded"
                />

                <input
                  type="number"
                  placeholder="%"
                  value={item.manual_margin_percentage}
                  onChange={(e) => updateField(index, "manual_margin_percentage", e.target.value)}
                  className="border p-1 rounded"
                />

                <input
                  type="date"
                  value={item.start_date}
                  onChange={(e) => updateField(index, "start_date", e.target.value)}
                  className="border p-1 rounded"
                />

                <input
                  type="date"
                  value={item.end_date}
                  onChange={(e) => updateField(index, "end_date", e.target.value)}
                  className="border p-1 rounded"
                />

                <div className="p-1 font-semibold text-green-600">
                  {row.totalSell.toFixed(0)}
                </div>

                <button
                  onClick={() => removeRow(index)}
                  className="bg-red-500 text-white rounded px-2"
                >
                  X
                </button>

              </div>
            );
          })}

          <button
            onClick={addNewRow}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded"
          >
            + Add Row
          </button>
        </div>

      </div>

      <div className="w-1/4 p-6 bg-white shadow-lg sticky top-0 h-screen">

        <h2 className="text-xl font-bold mb-6">Summary</h2>

        <div className="space-y-4 text-sm">
          <div className="flex justify-between">
            <span>Total Cost</span>
            <span>{totals.cost.toFixed(0)}</span>
          </div>

          <div className="flex justify-between">
            <span>Total Sell</span>
            <span>{totals.sell.toFixed(0)}</span>
          </div>

          <div className="flex justify-between font-semibold text-green-600">
            <span>Total Profit</span>
            <span>{totals.profit.toFixed(0)}</span>
          </div>
        </div>

        <button
          onClick={saveQuotation}
          className="mt-8 w-full bg-green-600 text-white py-3 rounded-lg font-semibold"
        >
          Save Quotation
        </button>

      </div>

    </div>
  );
}
