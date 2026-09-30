import { Outlet } from "@tanstack/react-router";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
export function AppLayout() {
  return (
    <>
      <Header />
      <main id="main">
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
