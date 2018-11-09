async function getProducts() {
  return await $.get("/product")
}

$(document).ready(
  async (documentReadyEvent) => {
    for(product of await getProducts()) {
      $('ul').append(
        (
          () => {
            let content = ''
            for(key in product) content += `<b>${ key }</b> ${ product[key] }<br/>`
            return `<li>${ content }</li>`
          }
        )()
      )
    }
  }
)
