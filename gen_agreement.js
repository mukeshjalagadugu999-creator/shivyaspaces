const {
  Document, Packer, Paragraph, TextRun, AlignmentType, PageOrientation,
  BorderStyle, WidthType, Table, TableRow, TableCell, ShadingType
} = require('docx');
const fs = require('fs');

const d = JSON.parse(process.argv[2]);
const outPath = process.argv[3];

// ── Helpers ──────────────────────────────────────────────────────────────────
function p(children, opts) {
  return new Paragraph({ children: Array.isArray(children) ? children : [children], ...(opts||{}) });
}
function t(text, bold, size) {
  return new TextRun({ text: text||'', bold: !!bold, size: size||22, font: 'Times New Roman' });
}
function b(text, size) { return t(text, true, size||22); }
function space(before) { return new Paragraph({ children:[new TextRun('')], spacing:{ before: before||120 } }); }
function center(children, opts) {
  return new Paragraph({ children: Array.isArray(children)?children:[children], alignment: AlignmentType.CENTER, ...(opts||{}) });
}
function justify(children, opts) {
  return new Paragraph({ children: Array.isArray(children)?children:[children], alignment: AlignmentType.JUSTIFIED, ...(opts||{}) });
}

// ── Derived values ────────────────────────────────────────────────────────────
const lockMonths = d.lockin_months || '6';
const lockWord = lockMonths === '6' ? 'Six' : lockMonths === '11' ? 'Eleven' : lockMonths;
const enhPct = d.enhancement_pct || '8';
const rentDueDay = d.rent_due_day || '5th';
const noticePeriod = d.notice_period || '30 days';
const propertyFullAddress =
  `${d.prop_flat}, ${d.prop_floor}, ${d.prop_facing_type ? d.prop_facing_type+', ' : ''}${d.prop_building}, Site #37, Ambica Arcade Phase-1, ${d.prop_street}, near Brigade Orchid North gate, Devanahalli, Bangalore-${d.prop_pin}, ${d.prop_state}`;

// ── Document ─────────────────────────────────────────────────────────────────
const children = [

  // TITLE
  center(b('RENTAL AGREEMENT', 28)),
  space(80),

  // Preamble
  justify([
    t('This '), b('RENTAL AGREEMENT'), t(', is made and executed on this '),
    b(d.executed_date), t(' ("Agreement") at Bangalore and effective from '),
    b(d.effective_date), t(' by and')
  ]),
  space(80),
  center(b('BETWEEN')),
  space(80),

  // OWNER paragraph
  justify([
    b(`Mr. ${d.owner_name}`), t(`, Age: ${d.owner_age}, Residing at: ${d.owner_address}`),
    t('. '), t('Mobile: '), b(d.owner_mobile), t('.')
  ]),
  space(80),

  // HEREINAFTER LESSOR
  justify([t('HEREINAFTER called the '), b('"LESSOR / OWNER / Landlord"'), t(' which expression shall unless repugnant to the meaning for content thereof, mean and include his executors, legal representatives, administrators, successors in title and assigns of the '), b('ONE PART.')]),
  space(80),

  p(b('AND')),
  space(80),

  // TENANT paragraph
  justify([
    b(`Mr. ${d.tenant_name}`), t(` (Aadhar No: ${d.tenant_aadhaar}) and PAN No: (${d.tenant_pan}), S/O: ${d.tenant_father}, ${d.tenant_address}.`),
    t(' Mobile: '), b(d.tenant_mobile)
  ]),
  space(80),

  // HEREINAFTER LESSEE
  justify([t('HEREINAFTER called the '), b('"LESSEE / TENANT"'), t(' which expression shall unless repugnant to the meaning for content thereof, mean and include his executors, legal representatives, administrators, successors in title and assigns of the '), b('OTHER/SECOND PART.')]),
  space(80),

  // WHEREAS
  justify([t('WHEREAS the Lessor is the absolute owner of property bearing: '), b(propertyFullAddress), t(', Karnataka. More fully described in the Schedule given hereunder and hereinafter referred to as the Schedule Property.')]),
  space(80),

  justify([t('AND WHEREAS the Lessee is in need of accommodation for his residential purpose and the Lessee has approached the Lessor for the grant of the lease of the Schedule Property, and the Lessor has agreed for the same.')]),
  space(80),

  justify([t('Which is more fully described in the schedule herein under and hereinafter referred to as the schedule property/flat and whereas accordingly this agreement witness that the Lessee hereby agreed to occupy the schedule property/flat on the terms and conditions hereinafter mentioned.')]),
  space(80),

  justify([b('NOW THEREFORE IT IS HEREBY AGREED TO, DECLARED AND RECORDED BY AND BETWEEN THE PARTIES HERETO THIS RENTAL AGREEMENT AND WITNESS AS FOLLOWS')]),
  space(80),

  // CLAUSE 1
  p([b('1. Duration:')]),
  justify([t('That the Lessor hereby allow the Lessee herein a revocable leave and license, to occupy the licensed premises, described in the scheduled property hereunder written without creating any tenancy rights or any other grants/rights, titles and interest in favour of Lessee.')]),
  space(60),
  justify([t('The duration of the lease will be initially for a period of maximum 11 months commencing from '), b(d.effective_date), t(` and is subject to renewal for a further period of 11 months with an increase in rent of ${enhPct}.0% on mutually agreeable and renewable according to the mutual understanding of both the parties by executing a fresh Rental Agreement, fulfilling statutory requirement and the expenses shall be met by the LESSEE terms & conditions.`)]),
  space(80),

  // CLAUSE 2
  p([b('2. Rent:')]),
  justify([t('The monthly advance rent (pay & stay) payable by the Lessee to the Lessor for the schedule property shall be '), b(`Rs. ${d.monthly_rent} `), t(`as a rent per month, excluding of electricity, internet, cable T.V fee and gas charges. Incase if the owner's association/ Community/builder takes a decision in the future considering the market increase and labor demand on the maintenance charges then LESSOR will inform the same to LESSE on the same who (LESSEE) needs to pay the maintenance charges per month accordingly.`)]),
  space(60),
  justify([t(`The advance rent shall be payable by Lessee before ${rentDueDay} of every English calendar month to be credited directly to the LESSOR\'s following account. No exceptions/exemptions are allowed considering any other circumstances like natural climates, COVID-19 or any other Govt. imposed rules until agreed with Lessor/Owner.`)]),
  space(60),
  justify([t('If the Lessee delays payment of the advance Rent beyond the timeline specified for any month, the Lessor shall be entitled to receive an interest at 18% per annum for the period of delay days.')]),
  space(60),
  justify([t('The electricity arrangement (more explained in Temporary Common Electricity Supply & Cost Sharing section) is temporary until a permanent dedicated direct meter connection is installed/commenced. Upon activation of the direct meter connection, the monthly rent will be auto revised to '), b(`₹${d.monthly_rent_revised} `), t('and the tenant shall pay the electricity charges directly to BESCOM based on actual consumption.')]),
  space(80),

  // CLAUSE 3
  p([b('3. Lock-in Period:')]),
  justify([t(`The Parties agree that neither Party shall be entitled to terminate this Agreement for a period of ${lockMonths} (${lockWord}) months starting with effect from the Commencement Date (i.e., from `), b(d.effective_date), t(` till `), b(d.lockin_end_date), t(') ("Lock-in Period"). In the event, the Lessee terminates the Agreement before the expiry of the Lock-in Period, the Lessor shall be entitled to deduct the Security Deposit in addition to the rent payable for the Notice Period as follows:')]),
  space(40),
  justify([t('(a) If the termination date falls within one month from the lock in expiry date, an amount equivalent to one month\'s rent shall be deducted from the Security Deposit')]),
  space(40),
  justify([t('(b) If the termination date exceeds one month from the rental expiry date, an amount equivalent to two months\' rent shall be deducted from the Security Deposit.')]),
  space(80),

  // CLAUSE 4
  p([b('4. Enhancement:')]),
  justify([t(`The rent payable to the LESSOR by the LESSEE as aforesaid in Clause No.1 shall be enhanced by ${enhPct}% (${enhPct === '8' ? 'Eight' : enhPct} Percent) of the last amount paid at the end of 11 months, subject to the renewal of the rental agreement by mutual consent of both the parties.`)]),
  space(80),

  // CLAUSE 5
  p([b('5. Interest Free Security Deposit:')]),
  justify([t('An interest free security deposit of '), b(`Rs. ${d.security_deposit} `), t('by way of account transfer from Lessee to Lessor account online. The same will be refundable by the lessor to the lessee at the time of vacating the scheduled property (termination of tenancy agreement). The possession of the property is deemed complete only upon handover of all keys. The deposit shall be refunded within 7 days of vacating the premises & hand over the keys after adjustment all dues.')]),
  space(60),
  justify([t('To the LESSOR as security deposit, which the LESSOR hereby acknowledges the said amount and the same shall be held by the LESSOR as Security Deposit during the continuance of the tenancy and/or any extension thereof and shall be repaid to the LESSEE free of interest at the end of the period of the lease, at the time of LESSEE vacating and delivering the said premises in the same condition, in which it was let out, or on termination of this agreement and after deducting the dues payable (like rent, maintenance, electricity, internet, damages and other arrears), if any, by the LESSEE to the LESSOR, painting/deep cleaning of the house and cost of rectification of any damages done.')]),
  space(80),

  // CLAUSE 6
  p([b('6. Temporary Common Electricity Supply & Cost Sharing Temporary Electricity Arrangement:')]),
  justify([t('The Lessee is aware that, as on the date of execution of this Agreement, the building is supplied with a temporary sanctioned common electrical load of 1 KW, which is shared by all occupants of the building. Separate permanent electricity meter connections for individual flats have been applied for with BESCOM and are awaited.')]),
  space(60),
  justify([t('Towards the common electricity expenses, the Lessee agrees to pay a fixed monthly contribution of Rs. 1,000/- (Rupees One Thousand only) along with the monthly rent/license fee, until individual permanent meters are installed.')]),
  space(60),
  justify([t('Upon installation/commission of dedicated permanent electricity meter(s) for the Schedule Property (individual flats) by BESCOM, this temporary electricity arrangement shall automatically stand terminated, and electricity charges shall thereafter be paid directly by the Lessee as per the individual consumption usage, meter readings and bills.')]),
  space(80),

  // CLAUSE 7
  p([b('7. Gas / Electricity / Internet / Cable T.V:')]),
  justify([t('The Lessee shall maintain the schedule property in a state of good housekeeping and condition. The LESSEE shall bear and pay the charges for the Electricity bill, Internet bill & Gas bill for the premised shall be borne by the Lessee based on the usage/fixed by the Owner welfare association / Builder (if association not yet formed) / respective authorities/suppliers on every month along with Rentals.')]),
  space(80),

  // CLAUSE 8
  p([b('8. Property Tax:')]),
  justify([t('The property tax and all other taxes, rates, cesses, assessments, duties and other outgoing payable related to municipal Corporation/ Grama Panchayat or any other authority of the government shall be borne by the LESSOR.')]),
  space(80),

  // CLAUSE 9
  p([b('9. Internal Maintenance:')]),
  justify([t('The Lessee shall maintain the schedule property in a state of good order and condition and shall not cause any damage to disfigurement to the schedule property or to any wall paintings, wardrobes, kitchen wood works, bath room, fittings and fixtures (as listed at the end of this contract) therein always. Any damage caused by the Lessee shall be made good by the Lessee or an equivalent amount will be deducted from the security deposit at the time of vacating the scheduled property.')]),
  space(60),
  justify([t('Repairs And Maintenance: It is specifically agreed between the parties to this deed that the cost of repairs and maintenance of the furniture, fixtures, electrical fittings like bulbs, tube lights, fans, fan regulators, etc. and water fittings like taps, shower, faucets, cistern, etc. shall be borne by the Lessee alone. However, problems related to civil and construction work, concealed electrical wiring and concealed plumbing, seepage and leakage of walls, ceiling or any part of the Schedule Property, shall be handled and set right by the Lessors at their own cost. However, the Lessors shall ensure that electrical fittings like tube lights, bulbs, fans and fan regulators, call bell etc. and sanitary fixtures like taps, cisterns, showers, geysers etc. are in perfectly working condition, at the time of handing over the schedule property to the Lessee, failing which, the Lessee is at liberty to get the same repaired or replaced and recover this cost from the Lessors. At the time of vacating the Schedule Property and handing it back to the Lessors, the Lessee shall ensure that all electrical and sanitary fittings are in the same working condition, The Lessees will ensure that the Schedule Property is handed over back to the Lessors in neat and tidy condition and all trash like bottles, cardboard and corrugated boxes, old newspapers, batteries adhesive packing tapes, used bulbs, tube lights, buckets, plastic mugs, toilet brushes, scrubbers, detergents and any type of junk is completely cleared before vacating the Schedule property. Excessive nailing in the Schedule Property and disfiguring of any part of the Schedule Property IN ANY MANNER, thus rendering it non-tenantable, is strictly inadmissible, failing which, the Lessee shall bear the entire cost of repairing to restore THIS damage caused, to its perfect condition. The Lessee shall not cause damage to the Schedule Property during his occupation of the Schedule Property. After ensuring that there are no damages or arrears OR after adjusting the cost of the damages and/or arrears, the balance or full amount (AS THE CASE MAY BE) will be refunded by the Lessor to the Lessee immediately the Lessee vacates the Schedule Property.')]),
  space(80),

  // CLAUSE 10
  p([b('10. Additions & Alterations:')]),
  justify([t('The Lessee shall not be entitled to make any additions or alteration internal and/or external to the said Scheduled premises and to the furniture, fixtures and electrical fittings installed/provided by the LESSOR at the Scheduled Premises which involves structural changes or not. The Lessee shall however be entitled to fix telephones, televisions, etc in the provision already given in the scheduled property. The Lessee shall be entitled to remove the same at the time of vacating the schedule property and shall be made good to the full satisfaction of the Lessor. The LESSEE shall ensure that the damages to walls and fixtures, if any, are duly repaired before handing over the possession.')]),
  space(80),

  // CLAUSE 11
  p([b('11. Nature of Usage / Purpose permitted:')]),
  justify([t('The Lessee shall use the schedule property only for Residential Purpose and that too with a family. The Lessee shall not keep or store in or upon any part of the schedule premises any goods of combustible or explosive nature, except those for cooking purposes and shall not store any offensive items, which may cause damage to the house premises and/or shall not carry any business activities either legal or illegal or un-lawful and illegitimate activities. Any kind of disturbance, misbehavior, unethical practice may call for immediate termination of agreement and evacuation from the property with a penalty of three months rental deducted from the advance security amount.')]),
  space(80),

  // CLAUSE 12
  p([b('12. No Tenancy:')]),
  justify([t('The LESSEE will not have any right to transfer, assign, and sub-let or grant any license or sub-license in respect of the scheduled property and premises or any part thereof and also shall not mortgage or raise any loan against the said premises. The LESSEE shall use the Scheduled Premises in a reasonable manner without causing any disturbance to the neighbors and agree to abide by the rules and regulations of Ambika Arcade Owners Association. That, the Lessee shall not claim any tenancy rights.')]),
  space(80),

  // CLAUSE 13
  p([b('13. Inspection:')]),
  justify([t('The Lessee shall permit the Lessor or his/her designated representatives, during the reasonable hours in the day time and upon making prior (at least 2 days in advance) appointment with Lessee to visit / inspect the schedule property and Lessor will permit (without any excuses what so ever) the Lessor to carry out such works within the schedule property, which are required for the general upkeep of the whole.')]),
  space(80),

  // CLAUSE 14
  p([b('14. Termination / Expiry / Revocation of the Lease:')]),
  justify([t(`The agreement shall be liable to be terminated by either Lessee or the Lessor by giving minimum of ${noticePeriod} of written (by mail/WhatsApp/call) notice. Since the Lessor have freshly painted the Schedule Property before handing it over to the Lessee, an amount equivalent to ONE MONTH rent (`), b(`Rs.${d.monthly_rent_revised}/-`), t(`) prevailing at the time of the Lessee vacating the Schedule Property shall be deducted as repainting charges by the Lessor from the interest free refundable deposit of the Lessee or Lessee can also repaint the house on vacating time then there is No deduction for painting. Any damages, Electricity bills, Gas bills, water bills, Unpaid Rents and any other due charges, amount will be deducted from the LESSEE\'s security deposit at the time of vacating the schedule premises. If in case, Lessee not able to vacate the said premises in the given vacant date then lessor shall be entitled to receive an interest at 18% per annum on the rent for the period of extension/delay.`)]),
  space(80),

  // CLAUSE 15
  p([b('15. Vacant Possession:')]),
  justify([t('The Lessor has delivered vacant possession of the Schedule Property to the Lessee this day pursuant to this deed. The Lessee shall deliver back vacant possession of the Schedule Property to the Lessor after the expiry of the period of lease fixed under this deed. The Lessee shall ensure that while vacating the schedule property all electrical fittings, plumber fittings, kitchen fittings, furniture fittings, all other fittings of the apartment as per delivered conditions and in case any damage etc found shall be replaced as per the original conditions.')]),
  space(80),

  // CLAUSE 16
  p([b('16. Breach Of Contract:')]),
  justify([t(`In the event of the Lessee committing breach of any of the terms and conditions contained in this deed, the Lessor is at liberty to terminate the lease and seek vacant possession of the Schedule Property from the Lessee even before the expiry of the period of lease fixed under this deed by immediately giving ${noticePeriod} notice. If the Lessee fails to pay the monthly rent to the Lessor, for more than two consecutive months, the Lessor reserves the right to terminate this contract and seek vacant possession of the Schedule Property from the Lessee, even before expiry of the period of lease fixed under this deed by immediately giving ${noticePeriod}' notice.`)]),
  space(80),

  // CLAUSE 17
  p([b('17. Termination Notice:')]),
  justify([t(`It is agreed that the contract entered into under this deed, can be terminated by either of the parties at any time, by giving ${noticePeriod} notice in writing.`)]),
  space(40),
  justify([t('The Rental Agreement shall be terminated under all or any of the following circumstances, namely.')]),
  space(40),
  justify([t('   i.  By efflux of time;')]),
  justify([t('   ii. In the event of breach by either party of the terms, conditions and covenants hereof;')]),
  justify([t(`   iii. By giving ${noticePeriod} prior notice from either party.`)]),
  space(80),

  // CLAUSE 18
  p([b('18. Renewal Of Lease Deed:')]),
  justify([t(`After expiry of the period of lease, if the Lessor and the Lessee agree to renew this contract, the hike in the monthly rent payable by the Lessee to the Lessor shall be ${enhPct}% (${enhPct === '8' ? 'Eight' : enhPct} percent) of the monthly rent (fixed during the first term) for these mutual discussions.`)]),
  space(80),

  // CLAUSE 19
  p([b('19. Representation:')]),
  justify([t('PROVIDED ALWAYS THAT whenever such an interpretation would be requisite to give fullest scope and effect legally possible, for any covenant or contract herein contained the expression \'LESSOR\' shall mean and include his heirs, legal representatives, successors and assigns and the expression \'LESSEE\' shall mean & include his heirs & legal representatives only.')]),
  space(80),

  // CLAUSE 20
  p([b('20. Jurisdiction:')]),
  justify([t('This Lease Deed is subject to the exclusive courts of Bangalore jurisdiction only.')]),
  space(80),

  // CLAUSE 21
  p([b('21. Liability:')]),
  justify([t('That if the Schedule Property or any part thereof be destroyed or damaged by fire (not caused by any wilful act or negligence) OR earthquake, tempest, flood, lightning, violence of any army or mob or enemies of the country or by any other irresistible force so as to render the Schedule property unfit for the purpose for which the same are let, either party shall have the option to forthwith terminate this Lease notwithstanding notice period provided in the Lease Deed. Upon this all the refundable securities shall be refunded immediately subject to any deductions / adjustments under this lease deed. The Lessor shall not be responsible or liable for any theft, loss, damage or destruction of any property of the Lessee or of any other person lying in the Schedule Property nor for any bodily injury or harm to/death of any person in the Schedule property from any cause whatsoever.')]),
  space(80),

  // CLAUSE 22
  p([b('22. Possession:')]),
  justify([t('That, the immediately at on the expiration or termination or cancellation of this agreement the Lessee shall vacate the said scheduled property and its premises without delay with all his goods and belongings. In the event of the Lessee failing and / or neglecting to remove him/herself and/or his/her articles/goods from the said & premises on expiry or sooner termination of this Agreement, the Lessor shall be entitled to recover damages at the rate of double the daily amount of compensation/rent per day and or alternatively the Lessor shall be entitled to remove the Lessee and his belongings from the Licensed premises, without recourse to the Court of Law and upon which the LESSOR shall return the remaining Security Deposit free of interest less any deduction shall be refunded one week after vacating the premises to the LESSEE.')]),
  space(80),

  // CLAUSE 23
  p([b('23. Fixtures:')]),
  justify([t('That the Lessee has seen before occupying the said scheduled property that all the sanitary and electric fittings and fixtures (details are clearly mentioned below) are in very good working condition and are satisfied that nothing is broken or missing and the Lessee on vacating the demised scheduled property premises shall restore them, in the same condition, subject to normal wear and tear.')]),
  space(80),

  // CLAUSE 24
  p([b('24. MOVE-IN and MOVE-OUT Charges:')]),
  justify([t('All costs & association charges relating to shifting in and shifting out of the community/complex shall always be borne by the LESSEE.')]),
  space(80),

  // CLAUSE 25
  p([b('25. Peaceful Stay:')]),
  justify([t('The Lessor hereby assures the Lessee that on performance of the terms and conditions contained in this deed by the Lessee, the Lessee shall quietly enjoy the Schedule Property, without any hindrance either by the Lessor or from anybody else claiming through or under the Lessor. The tenant shall not cause any disturbance and live peacefully without harming the interest of neighbors and by fulfilling the above terms and conditions regularly without default.')]),
  space(80),

  // CLAUSE 26
  p([b('26. Water Charges:')]),
  justify([t('Currently, no water charges are applicable. However, the association is in discussions regarding the introduction of water charges very soon. If any such charges are implemented in future, the same will be communicated separately and shall be payable by lessee on a monthly basis along with Rent, electricity amount.')]),
  space(80),

  // CLAUSE 27
  p([b('27. Cleaning Responsibility:')]),
  justify([t('Cleaning of the staircase area from the 1st floor up to the next (2nd) floor mid steps will be the responsibility of the respective tenant. If tenants are not agreeable to this arrangement, a cleaner will be arranged for common area maintenance (parking, staircase, common areas etc.), and the cleaning charges will be shared equally among all tenants.')]),
  space(120),

  // SCHEDULE
  center(b('SCHEDULE')),
  space(80),
  justify([t('The Residential Premises bearing '), b(propertyFullAddress), t(', Karnataka., comprising of one living room, one kitchen with Utility area, one bedroom, one bathroom and one pooja Cabinet.')]),
  space(80),

  justify([t('IN WITNESS WHEREOF, both the Lessor and the Lessee have affixed their respective hands and signature to this agreement on this day, month and year first above written.')]),
  space(80),

  p(b('WITNESSES:')),
  space(40),
  p([t(`1) ${d.owner_name}`)]),
  p([t(`   Mob# ${d.owner_mobile}`)]),
  p([t('   '), b('LESSOR')]),
  space(60),
  p([t(`2) ${d.tenant_name}.`)]),
  p([t(`   Aadhar ID # ${d.tenant_aadhaar}`)]),
  p([t(`   Mob # ${d.tenant_mobile}`)]),
  p([t('   '), b('LESSEE')]),
  space(120),

  // SCHEDULE PREMISES — FITTINGS
  center(b('SCHEDULE PREMISES')),
  center(b('FITTINGS & FIXTURE IN SCHEDULED PREMISES')),
  space(80),

  p([b('Hall Area:'), t('                                    '), b('Kitchen:')]),
  p([t(`Foyer Light: ${d.hall_foyer_light}                                   Modular kitchen with Glasses: ${d.kitchen_modular}`)]),
  p([t(`Tube Light: ${d.hall_tube_light}                                     LED/Zoomer Light: ${d.kitchen_led}`)]),
  p([t(`LED/Zoomer Light: ${d.hall_led_light}                                 LED/Zoomer Light in Utility: ${d.kitchen_led_utility}`)]),
  p([t(`Curtain Rod: ${d.hall_curtain_rod}`)]),
  p([t(`Wall Mounted Bulb: ${d.hall_wall_bulb}`)]),
  p([t(`Fan: ${d.hall_fan}`)]),
  p([t(`TV Cabinet with Glasses: ${d.hall_tv_cabinet}`)]),
  p([t(`UPS Point: ${d.hall_ups}`)]),
  p([t(`Bell: ${d.hall_bell}`)]),
  p([t(`False Ceiling/POP Lights: ${d.hall_pop_lights}`)]),
  space(60),

  p(b('Pooja Mandir:')),
  p([t(`Pooja Mandir structure set-up: ${d.pooja_structure}`)]),
  p([t(`Storage Box/Drawers: ${d.pooja_storage}`)]),
  p([t(`Pooja Bulb: ${d.pooja_bulb}`)]),
  space(60),

  p([b('Bedroom:'), t('                                          '), b('')]),
  p([t(`Fan: ${d.bed_fan}                                                    Tube light: ${d.bed_tube}`)]),
  p([t(`Curtain rod: ${d.bed_curtain}                                        Loft: ${d.bed_loft}`)]),
  p([t(`Sliding Lock: ${d.bed_sliding_lock}                                  Drawer Locker: ${d.bed_drawer_locker}`)]),
  p([t(`Dressing Glass: ${d.bed_dressing}                                    Bangles Rod: ${d.bed_bangles_rod}`)]),
  p([t(`Hanger Rod: ${d.bed_hanger}                                          Bulb: ${d.bed_bulb}`)]),
  p([t(`Ceiling Light: ${d.bed_ceiling}                                      Sitting Desk: ${d.bed_desk}`)]),
  space(60),

  p(b('Bathroom:')),
  p([t(`Storage Box (with 1 Mirror): ${d.bath_storage}                       Geyser: ${d.bath_geyser}`)]),
  p([t(`Bulb: ${d.bath_bulb}                                                 Ceiling Light: ${d.bath_ceiling}`)]),
  p([t(`Exhaust Fan: ${d.bath_exhaust}`)]),
  space(60),

  p(b('Total Keys of Flat:')),
  p([t(`Main Door: ${d.key_main_num} (${d.key_main_qty})                     Bedroom: ${d.key_bedroom_num} (${d.key_bedroom_qty})`)]),
  p([t(`Sliding Door Lock: ${d.key_sliding_num} (${d.key_sliding_qty})       Drawer Lock: ${d.key_drawer_num} (${d.key_drawer_qty})`)]),

];

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: 'Times New Roman', size: 22 } }
    }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1080, bottom: 1440, left: 1440 }
      }
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log('OK');
}).catch(err => {
  process.stderr.write(err.toString());
  process.exit(1);
});