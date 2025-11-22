import fitz
import sys
import os

def extract_clean_layers_batch(input_pdf_path, output_dir):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Get total pages first
        doc_info = fitz.open(input_pdf_path)
        total_pages = len(doc_info)
        doc_info.close()
        
        print(f"Processing {total_pages} pages from {input_pdf_path}...")

        for i in range(total_pages):
            try:
                # Open fresh for each page to ensure clean state
                doc = fitz.open(input_pdf_path)
                
                # Select the current page (keeps only this page)
                doc.select([i])
                page = doc[0] 
                
                # --- Layer Cleanup Logic ---
                
                # Get all OCGs
                all_ocgs = doc.get_ocgs() # dict {xref: name, ...}
                
                # Get page resources string
                res_xref = -1
                res_obj = doc.xref_get_key(page.xref, "Resources")
                if res_obj[0] == "xref":
                    res_xref = int(res_obj[1].split()[0])
                    res_content = doc.xref_object(res_xref)
                else:
                    res_content = res_obj[1]
                    
                used_ocg_xrefs = []
                for xref in all_ocgs:
                    if f"{xref} 0 R" in res_content:
                        used_ocg_xrefs.append(xref)
                        
                # Rebuild OCProperties
                def format_refs(xrefs):
                    return "[" + " ".join([f"{x} 0 R" for x in xrefs]) + "]"
                    
                ocgs_str = format_refs(used_ocg_xrefs)
                
                new_oc_props = f"""<<
  /OCGs {ocgs_str}
  /D <<
    /Order {ocgs_str}
    /Name (Default)
  >>
>>"""

                # Update the Catalog
                catalog_xref = doc.pdf_catalog()
                doc.xref_set_key(catalog_xref, "OCProperties", new_oc_props)
                
                # --- Save ---
                
                output_filename = f"page_{i+1}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                doc.save(output_path)
                print(f"Saved Page {i+1} to {output_path} ({len(used_ocg_xrefs)} layers)")
                doc.close()
                
            except Exception as e:
                print(f"Error processing page {i+1}: {e}")
                
    except Exception as e:
        print(f"Fatal Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_clean_layers.py <input_pdf> <output_directory>")
    else:
        extract_clean_layers_batch(sys.argv[1], sys.argv[2])
