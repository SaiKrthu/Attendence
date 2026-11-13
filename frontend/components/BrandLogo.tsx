import Image from "next/image";
import Link from "next/link";

export default function BrandLogo() {
  return (
    <Link aria-label="RGES Attendance Portal home" className="brand-logo" href="/">
      <Image
        alt="Risk Guard Enterprise Solutions"
        height={200}
        priority
        src="/rges-logo.png"
        width={900}
      />
      <span className="brand-copy">
        <strong>RGES Attendance Portal</strong>
        <small>WORKFORCE MANAGEMENT</small>
      </span>
    </Link>
  );
}
